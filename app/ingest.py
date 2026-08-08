"""Download dataset, ingest with chosen compression, run processing."""
from __future__ import annotations

import io
import time
from pathlib import Path
from typing import Any, Callable

import httpx
import numpy as np
import pandas as pd

from app import (
    DATASET_CANDIDATES,
    DEFAULT_DATASET_NAME,
    DEFAULT_DATASET_URL,
    PROCESSED_DIR,
    RAW_DIR,
)
from app.formats import extension_for, read_frame, write_frame
from app.metrics import MetricsCollector, RunResult, timed_stage


ProgressCb = Callable[[dict[str, Any]], None]


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)


def generate_synthetic(n_rows: int = 200_000) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    return pd.DataFrame(
        {
            "trip_id": np.arange(n_rows),
            "vendor": rng.integers(1, 5, size=n_rows),
            "distance_km": rng.random(n_rows) * 30,
            "fare": rng.random(n_rows) * 80 + 2,
            "tip": rng.random(n_rows) * 15,
            "passengers": rng.integers(1, 6, size=n_rows),
            "hour": rng.integers(0, 24, size=n_rows),
            "weekday": rng.integers(0, 7, size=n_rows),
        }
    )


def _try_download_one(
    url: str,
    dest: Path,
    collector: MetricsCollector | None = None,
    on_progress: ProgressCb | None = None,
) -> Path:
    with httpx.stream("GET", url, follow_redirects=True, timeout=60.0) as resp:
        resp.raise_for_status()
        total = int(resp.headers.get("content-length") or 0)
        done = 0
        with open(dest, "wb") as f:
            for chunk in resp.iter_bytes(1024 * 64):
                f.write(chunk)
                done += len(chunk)
                if collector:
                    collector.add_bytes(len(chunk))
                if on_progress and total:
                    on_progress(
                        {
                            "stage": "download",
                            "status": "running",
                            "bytes": done,
                            "total": total,
                            "pct": round(100 * done / total, 1),
                            "url": url,
                        }
                    )
    return dest


def download_dataset(
    url: str = DEFAULT_DATASET_URL,
    dest_name: str = DEFAULT_DATASET_NAME,
    collector: MetricsCollector | None = None,
    on_progress: ProgressCb | None = None,
) -> Path:
    ensure_dirs()
    # Prefer any already-downloaded real CSV (not synthetic) if present
    for _, name in DATASET_CANDIDATES:
        existing = RAW_DIR / name
        if existing.exists() and existing.stat().st_size > 0:
            if on_progress:
                on_progress({"stage": "download", "status": "cached", "path": str(existing)})
            return existing

    if collector:
        collector.set_stage("download")

    candidates = [(url, dest_name)] + [c for c in DATASET_CANDIDATES if c[0] != url]
    errors: list[str] = []
    for cand_url, cand_name in candidates:
        dest = RAW_DIR / cand_name
        try:
            if on_progress:
                on_progress({"stage": "download", "status": "trying", "url": cand_url})
            return _try_download_one(cand_url, dest, collector=collector, on_progress=on_progress)
        except Exception as exc:
            errors.append(f"{cand_url}: {exc}")
            if dest.exists():
                dest.unlink(missing_ok=True)

    # Fallback: larger synthetic taxi so compression trade-offs still show up
    if on_progress:
        on_progress({"stage": "download", "status": "fallback", "error": "; ".join(errors)})
    df = generate_synthetic(250_000)
    dest = RAW_DIR / "synthetic_taxi.csv"
    df.to_csv(dest, index=False)
    return dest


def load_raw_dataframe(path: Path, max_rows: int | None = None) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, nrows=max_rows)
    if path.suffix.lower() in {".parquet"}:
        import pyarrow.parquet as pq

        table = pq.read_table(path)
        df = table.to_pandas()
        return df.head(max_rows) if max_rows else df
    # try csv
    return pd.read_csv(path, nrows=max_rows)


def light_analytics(df: pd.DataFrame) -> dict[str, Any]:
    """CPU+RAM work that benefits from columnar access."""
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return {"rows": len(df)}
    # Prefer a few columns if present
    cols = [c for c in ["fare", "tip", "distance_km", "passengers"] if c in numeric.columns]
    if not cols:
        cols = list(numeric.columns[:4])
    sub = numeric[cols]
    return {
        "rows": len(df),
        "sum": float(sub.sum().sum()),
        "mean": float(sub.mean().mean()),
        "groupby_hour_mean": (
            float(df.groupby("hour")[cols[0]].mean().mean())
            if "hour" in df.columns and cols
            else None
        ),
    }


def ingest_and_process(
    df: pd.DataFrame,
    *,
    fmt: str = "parquet",
    codec: str = "zstd",
    level: int | None = 5,
    threads: int = 4,
    name: str | None = None,
    collector: MetricsCollector | None = None,
    columns_for_read: list[str] | None = None,
    on_progress: ProgressCb | None = None,
) -> RunResult:
    ensure_dirs()
    original_bytes = int(df.memory_usage(deep=True).sum())
    # Also approximate CSV size for ratio vs "uncompressed on disk"
    csv_buf = io.StringIO()
    df.to_csv(csv_buf, index=False)
    csv_bytes = len(csv_buf.getvalue().encode("utf-8"))

    label = name or f"{fmt}-{codec}{('-' + str(level)) if codec == 'zstd' and level else ''}"
    out = PROCESSED_DIR / f"{label.replace('/', '_')}{extension_for(fmt)}"

    own_collector = collector is None
    if own_collector:
        collector = MetricsCollector()
        collector.start()

    write_s = read_s = proc_s = 0.0
    analytics: dict[str, Any] = {}

    try:
        if on_progress:
            on_progress({"stage": "write", "status": "running", "name": label})
        with timed_stage(collector, "write"):
            t0 = time.perf_counter()
            compressed_bytes = write_frame(
                df, out, fmt=fmt, codec=codec, level=level, threads=threads
            )
            write_s = time.perf_counter() - t0
            collector.add_bytes(compressed_bytes)

        if on_progress:
            on_progress({"stage": "read", "status": "running", "name": label})
        with timed_stage(collector, "read"):
            t0 = time.perf_counter()
            loaded = read_frame(out, fmt=fmt, columns=columns_for_read)
            read_s = time.perf_counter() - t0
            collector.add_bytes(csv_bytes)

        if on_progress:
            on_progress({"stage": "process", "status": "running", "name": label})
        with timed_stage(collector, "process"):
            t0 = time.perf_counter()
            analytics = light_analytics(loaded)
            proc_s = time.perf_counter() - t0
    finally:
        if own_collector and collector:
            collector.stop()

    summary = collector.summary() if collector else {}
    total = write_s + read_s + proc_s
    thr = (csv_bytes / (1024 * 1024)) / max(read_s + proc_s, 1e-9)

    return RunResult(
        name=label,
        codec=codec,
        level=level if codec == "zstd" else level,
        fmt=fmt,
        rows=len(df),
        original_bytes=csv_bytes,
        compressed_bytes=int(compressed_bytes),
        compression_ratio=round(csv_bytes / max(compressed_bytes, 1), 3),
        write_seconds=round(write_s, 4),
        read_seconds=round(read_s, 4),
        process_seconds=round(proc_s, 4),
        total_seconds=round(total, 4),
        throughput_mb_s=round(thr, 3),
        avg_cpu_percent=round(summary.get("avg_cpu_percent", 0.0), 2),
        avg_disk_wait_percent=round(summary.get("avg_disk_wait_percent", 0.0), 2),
        peak_rss_mb=round(summary.get("peak_rss_mb", 0.0), 2),
        threads=threads,
        notes=f"in_memory_df_bytes={original_bytes}",
        extra={"analytics": analytics, "path": str(out)},
    )
