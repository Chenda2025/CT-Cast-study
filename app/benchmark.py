"""Benchmark matrix, Zstd sweep, scale tests, compress-then-cache."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

from app import BENCHMARKS_DIR
from app.ingest import ingest_and_process, light_analytics
from app.metrics import MetricsCollector, RunResult
from app.recommend import recommend_best


ProgressCb = Callable[[dict[str, Any]], None]


def _slice_df(df: pd.DataFrame, n: int | None) -> pd.DataFrame:
    if n is None or n >= len(df):
        return df
    return df.iloc[:n].copy()


def run_codec_matrix(
    df: pd.DataFrame,
    *,
    fmt: str = "parquet",
    codecs: list[str] | None = None,
    zstd_level: int = 5,
    threads: int = 4,
    on_progress: ProgressCb | None = None,
) -> list[RunResult]:
    codecs = codecs or ["none", "snappy", "lz4", "zstd", "gzip", "brotli"]
    results: list[RunResult] = []
    for i, codec in enumerate(codecs):
        if on_progress:
            on_progress(
                {
                    "stage": "matrix",
                    "status": "running",
                    "codec": codec,
                    "index": i,
                    "total": len(codecs),
                }
            )
        level = zstd_level if codec == "zstd" else (6 if codec in {"gzip", "brotli"} else None)
        # CSV format ignores codec — only run once for uncompressed baseline
        use_fmt = "csv" if codec == "none" and fmt == "parquet" else fmt
        if codec == "none":
            use_fmt = "csv"
        try:
            r = ingest_and_process(
                df,
                fmt=use_fmt,
                codec=codec if use_fmt != "csv" else "none",
                level=level,
                threads=threads,
                name=f"matrix-{use_fmt}-{codec}",
                on_progress=on_progress,
            )
            results.append(r)
        except Exception as exc:
            results.append(
                RunResult(
                    name=f"matrix-{fmt}-{codec}",
                    codec=codec,
                    level=level,
                    fmt=use_fmt if codec == "none" else fmt,
                    rows=len(df),
                    original_bytes=0,
                    compressed_bytes=0,
                    compression_ratio=0.0,
                    write_seconds=0.0,
                    read_seconds=0.0,
                    process_seconds=0.0,
                    total_seconds=0.0,
                    throughput_mb_s=0.0,
                    avg_cpu_percent=0.0,
                    avg_disk_wait_percent=0.0,
                    peak_rss_mb=0.0,
                    threads=threads,
                    notes=f"error: {exc}",
                )
            )
    return results


def run_zstd_sweep(
    df: pd.DataFrame,
    *,
    fmt: str = "parquet",
    levels: list[int] | None = None,
    threads: int = 4,
    on_progress: ProgressCb | None = None,
) -> list[RunResult]:
    # Full 1–22 can be slow; default to representative + allow full via UI
    levels = levels or [1, 3, 5, 7, 9, 12, 15, 18, 22]
    results: list[RunResult] = []
    for i, level in enumerate(levels):
        if on_progress:
            on_progress(
                {
                    "stage": "zstd_sweep",
                    "status": "running",
                    "level": level,
                    "index": i,
                    "total": len(levels),
                }
            )
        r = ingest_and_process(
            df,
            fmt=fmt,
            codec="zstd",
            level=level,
            threads=threads,
            name=f"zstd-{fmt}-L{level}",
            on_progress=on_progress,
        )
        results.append(r)
    return results


def run_scale_sweep(
    df: pd.DataFrame,
    *,
    fmt: str = "parquet",
    codec: str = "zstd",
    level: int = 5,
    sizes: list[int] | None = None,
    threads: int = 4,
    on_progress: ProgressCb | None = None,
) -> list[RunResult]:
    n = len(df)
    sizes = sizes or sorted({min(10_000, n), min(50_000, n), min(150_000, n), n})
    results: list[RunResult] = []
    for i, size in enumerate(sizes):
        if on_progress:
            on_progress(
                {
                    "stage": "scale",
                    "status": "running",
                    "rows": size,
                    "index": i,
                    "total": len(sizes),
                }
            )
        part = _slice_df(df, size)
        r = ingest_and_process(
            part,
            fmt=fmt,
            codec=codec,
            level=level,
            threads=threads,
            name=f"scale-{size}-{codec}",
            on_progress=on_progress,
        )
        results.append(r)
    return results


def run_compress_then_cache(
    df: pd.DataFrame,
    *,
    level: int = 5,
    on_progress: ProgressCb | None = None,
) -> list[RunResult]:
    """Compare uncompressed in-RAM vs Blosc2-compressed in-RAM then decompress on access."""
    import blosc2

    results: list[RunResult] = []
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        numeric = pd.DataFrame({"x": np.arange(len(df), dtype=np.float64)})
    arr = numeric.to_numpy(dtype=np.float64, copy=True)
    raw_bytes = arr.nbytes

    # Uncompressed cache
    if on_progress:
        on_progress({"stage": "cache", "status": "uncompressed"})
    collector = MetricsCollector()
    collector.start()
    t0 = time.perf_counter()
    collector.set_stage("process")
    cache_raw = arr.copy()
    _ = light_analytics(pd.DataFrame(cache_raw, columns=list(numeric.columns)))
    raw_s = time.perf_counter() - t0
    collector.stop()
    s = collector.summary()
    results.append(
        RunResult(
            name="cache-uncompressed-ram",
            codec="none",
            level=None,
            fmt="ram",
            rows=len(df),
            original_bytes=raw_bytes,
            compressed_bytes=raw_bytes,
            compression_ratio=1.0,
            write_seconds=0.0,
            read_seconds=0.0,
            process_seconds=round(raw_s, 4),
            total_seconds=round(raw_s, 4),
            throughput_mb_s=round((raw_bytes / (1024 * 1024)) / max(raw_s, 1e-9), 3),
            avg_cpu_percent=round(s["avg_cpu_percent"], 2),
            avg_disk_wait_percent=round(s["avg_disk_wait_percent"], 2),
            peak_rss_mb=round(s["peak_rss_mb"], 2),
            notes="baseline in-RAM uncompressed",
        )
    )

    # Compress-then-cache
    if on_progress:
        on_progress({"stage": "cache", "status": "compressed"})
    collector = MetricsCollector()
    collector.start()
    t0 = time.perf_counter()
    collector.set_stage("write")
    blosc2.set_nthreads(4)
    compressed = blosc2.pack_array(
        arr, clevel=min(9, level), codec=blosc2.Codec.ZSTD
    )
    pack_s = time.perf_counter() - t0
    t1 = time.perf_counter()
    collector.set_stage("read")
    restored = blosc2.unpack_array(compressed)
    collector.set_stage("process")
    _ = light_analytics(pd.DataFrame(restored, columns=list(numeric.columns)))
    unpack_s = time.perf_counter() - t1
    collector.stop()
    s = collector.summary()
    csize = len(compressed) if isinstance(compressed, (bytes, bytearray, memoryview)) else raw_bytes
    results.append(
        RunResult(
            name="cache-blosc2-zstd-ram",
            codec="zstd",
            level=level,
            fmt="ram-blosc2",
            rows=len(df),
            original_bytes=raw_bytes,
            compressed_bytes=int(csize),
            compression_ratio=round(raw_bytes / max(int(csize), 1), 3),
            write_seconds=round(pack_s, 4),
            read_seconds=round(unpack_s, 4),
            process_seconds=round(unpack_s, 4),
            total_seconds=round(pack_s + unpack_s, 4),
            throughput_mb_s=round((raw_bytes / (1024 * 1024)) / max(unpack_s, 1e-9), 3),
            avg_cpu_percent=round(s["avg_cpu_percent"], 2),
            avg_disk_wait_percent=round(s["avg_disk_wait_percent"], 2),
            peak_rss_mb=round(s["peak_rss_mb"], 2),
            threads=4,
            notes="compress-then-cache in RAM",
        )
    )
    return results


def run_thread_scaling(
    df: pd.DataFrame,
    *,
    fmt: str = "blosc2",
    level: int = 5,
    thread_counts: list[int] | None = None,
    on_progress: ProgressCb | None = None,
) -> list[RunResult]:
    thread_counts = thread_counts or [1, 2, 4, 8]
    results: list[RunResult] = []
    for i, tc in enumerate(thread_counts):
        if on_progress:
            on_progress(
                {
                    "stage": "threads",
                    "status": "running",
                    "threads": tc,
                    "index": i,
                    "total": len(thread_counts),
                }
            )
        r = ingest_and_process(
            df,
            fmt=fmt,
            codec="zstd",
            level=level,
            threads=tc,
            name=f"threads-{tc}",
            on_progress=on_progress,
        )
        results.append(r)
    return results


def save_results(payload: dict[str, Any], path: Path | None = None) -> Path:
    BENCHMARKS_DIR.mkdir(parents=True, exist_ok=True)
    path = path or (BENCHMARKS_DIR / "results.json")
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def full_benchmark_suite(
    df: pd.DataFrame,
    *,
    fmt: str = "parquet",
    zstd_levels: list[int] | None = None,
    threads: int = 4,
    on_progress: ProgressCb | None = None,
) -> dict[str, Any]:
    matrix = run_codec_matrix(df, fmt=fmt, threads=threads, on_progress=on_progress)
    sweep = run_zstd_sweep(
        df, fmt=fmt, levels=zstd_levels, threads=threads, on_progress=on_progress
    )
    scale = run_scale_sweep(df, fmt=fmt, threads=threads, on_progress=on_progress)
    cache = run_compress_then_cache(df, on_progress=on_progress)
    threads_r = run_thread_scaling(df, on_progress=on_progress)

    all_runs = matrix + sweep + scale + cache + threads_r
    recommendation = recommend_best(matrix + sweep)

    payload = {
        "matrix": [r.to_dict() for r in matrix],
        "zstd_sweep": [r.to_dict() for r in sweep],
        "scale": [r.to_dict() for r in scale],
        "compress_then_cache": [r.to_dict() for r in cache],
        "thread_scaling": [r.to_dict() for r in threads_r],
        "recommendation": recommendation,
        "rows": len(df),
    }
    save_results(payload)
    return payload
