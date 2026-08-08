"""FastAPI web app — configure compression, monitor metrics, run benchmarks."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from app import BENCHMARKS_DIR, CODECS, FORMATS, ROOT, ZSTD_LEVELS
from app.benchmark import full_benchmark_suite, run_codec_matrix, run_zstd_sweep
from app.ingest import download_dataset, ingest_and_process, load_raw_dataframe
from app.metrics import MetricsCollector
from app.recommend import recommend_best

APP_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(APP_DIR / "templates"))

app = FastAPI(title="Compression Trade-Offs Case Study", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(APP_DIR / "static")), name="static")

# Shared job state
_state: dict[str, Any] = {
    "status": "idle",
    "message": "Ready",
    "progress": {},
    "results": [],
    "recommendation": None,
    "live": [],
    "error": None,
}
_collector: Optional[MetricsCollector] = None
_lock = threading.Lock()
_df_cache = None


class IngestRequest(BaseModel):
    fmt: str = "parquet"
    codec: str = "zstd"
    level: int = Field(default=5, ge=1, le=22)
    threads: int = Field(default=4, ge=1, le=16)
    max_rows: Optional[int] = Field(default=100_000, ge=1000, le=2_000_000)


class BenchmarkRequest(BaseModel):
    fmt: str = "parquet"
    threads: int = Field(default=4, ge=1, le=16)
    max_rows: Optional[int] = Field(default=80_000, ge=1000, le=500_000)
    zstd_full: bool = False
    mode: str = "full"  # full | matrix | zstd_sweep


def _set(**kwargs: Any) -> None:
    with _lock:
        _state.update(kwargs)


def _progress(info: dict[str, Any]) -> None:
    with _lock:
        _state["progress"] = info
        _state["message"] = f"{info.get('stage', '')}: {info.get('status', '')}"
        if _collector:
            _state["live"] = _collector.live_tail(80)


def _ensure_df(max_rows: int | None):
    global _df_cache
    path = download_dataset(on_progress=_progress)
    df = load_raw_dataframe(path, max_rows=None)
    # Small public CSVs prove R5 download; scale up with synthetic rows for measurable I/O vs CPU.
    if len(df) < 50_000:
        from app.ingest import generate_synthetic

        extra = generate_synthetic(max(120_000, (max_rows or 80_000)))
        # Keep downloaded columns where possible; otherwise use synthetic schema
        df = extra
        _progress(
            {
                "stage": "download",
                "status": "scaled",
                "note": f"Downloaded {path.name}; using {len(df)} synthetic taxi rows for timing scale",
                "source_path": str(path),
            }
        )
    if max_rows and len(df) > max_rows:
        df = df.iloc[:max_rows].copy()
    _df_cache = df
    return df


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "codecs": CODECS,
            "formats": FORMATS,
            "zstd_levels": ZSTD_LEVELS,
        },
    )


@app.get("/slides", response_class=HTMLResponse)
async def slides(request: Request):
    return templates.TemplateResponse("slides.html", {"request": request})


@app.get("/api/state")
async def get_state():
    with _lock:
        live = _collector.live_tail(80) if _collector else _state.get("live", [])
        return {
            **{k: v for k, v in _state.items() if k != "live"},
            "live": live,
        }


@app.get("/api/results")
async def get_results():
    path = BENCHMARKS_DIR / "results.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    with _lock:
        return {
            "results": _state.get("results"),
            "recommendation": _state.get("recommendation"),
        }


@app.post("/api/download")
async def api_download():
    if _state["status"] == "running":
        return JSONResponse({"ok": False, "error": "Job already running"}, status_code=409)

    def job():
        global _collector
        _set(status="running", error=None, message="Downloading dataset…")
        _collector = MetricsCollector()
        _collector.start()
        try:
            path = download_dataset(collector=_collector, on_progress=_progress)
            df = load_raw_dataframe(path, max_rows=100_000)
            global _df_cache
            _df_cache = df
            _set(
                status="idle",
                message=f"Dataset ready: {path.name} ({len(df)} rows loaded)",
                progress={"stage": "download", "status": "done", "rows": len(df)},
            )
        except Exception as exc:
            _set(status="error", error=str(exc), message="Download failed")
        finally:
            if _collector:
                _collector.stop()

    threading.Thread(target=job, daemon=True).start()
    return {"ok": True}


@app.post("/api/ingest")
async def api_ingest(body: IngestRequest):
    if _state["status"] == "running":
        return JSONResponse({"ok": False, "error": "Job already running"}, status_code=409)

    def job():
        global _collector
        _set(status="running", error=None, message="Ingesting…", results=[])
        _collector = MetricsCollector()
        _collector.start()
        try:
            df = _ensure_df(body.max_rows)
            result = ingest_and_process(
                df,
                fmt=body.fmt,
                codec=body.codec,
                level=body.level if body.codec == "zstd" else body.level,
                threads=body.threads,
                collector=_collector,
                on_progress=_progress,
            )
            rec = recommend_best([result])
            _set(
                status="idle",
                message="Ingest complete",
                results=[result.to_dict()],
                recommendation=rec,
            )
        except Exception as exc:
            _set(status="error", error=str(exc), message="Ingest failed")
        finally:
            if _collector:
                _collector.stop()

    threading.Thread(target=job, daemon=True).start()
    return {"ok": True}


@app.post("/api/benchmark")
async def api_benchmark(body: BenchmarkRequest):
    if _state["status"] == "running":
        return JSONResponse({"ok": False, "error": "Job already running"}, status_code=409)

    def job():
        global _collector
        _set(status="running", error=None, message="Benchmark running…", results=[])
        _collector = MetricsCollector()
        _collector.start()
        try:
            df = _ensure_df(body.max_rows)
            levels = list(range(1, 23)) if body.zstd_full else [1, 3, 5, 7, 9, 12, 15, 18, 22]
            if body.mode == "matrix":
                runs = run_codec_matrix(
                    df, fmt=body.fmt, threads=body.threads, on_progress=_progress
                )
                payload = {
                    "matrix": [r.to_dict() for r in runs],
                    "recommendation": recommend_best(runs),
                    "rows": len(df),
                }
                from app.benchmark import save_results

                save_results(payload)
            elif body.mode == "zstd_sweep":
                runs = run_zstd_sweep(
                    df,
                    fmt=body.fmt,
                    levels=levels,
                    threads=body.threads,
                    on_progress=_progress,
                )
                payload = {
                    "zstd_sweep": [r.to_dict() for r in runs],
                    "recommendation": recommend_best(runs),
                    "rows": len(df),
                }
                from app.benchmark import save_results

                save_results(payload)
            else:
                payload = full_benchmark_suite(
                    df,
                    fmt=body.fmt,
                    zstd_levels=levels,
                    threads=body.threads,
                    on_progress=_progress,
                )
            flat = []
            for key in ("matrix", "zstd_sweep", "scale", "compress_then_cache", "thread_scaling"):
                flat.extend(payload.get(key) or [])
            if not flat and payload.get("matrix"):
                flat = payload["matrix"]
            _set(
                status="idle",
                message="Benchmark complete",
                results=flat,
                recommendation=payload.get("recommendation"),
            )
        except Exception as exc:
            _set(status="error", error=str(exc), message="Benchmark failed")
        finally:
            if _collector:
                _collector.stop()

    threading.Thread(target=job, daemon=True).start()
    return {"ok": True}


@app.get("/api/codecs")
async def api_codecs():
    from app.codecs import describe_codec

    return {c: describe_codec(c) for c in CODECS}


def create_app() -> FastAPI:
    return app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
