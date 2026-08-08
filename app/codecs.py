"""Codec helpers and Parquet/Feather compression name mapping."""
from __future__ import annotations

from typing import Any

# Parquet compression names accepted by pyarrow
PARQUET_CODECS = {
    "none": "NONE",
    "snappy": "SNAPPY",
    "lz4": "LZ4",
    "zstd": "ZSTD",
    "gzip": "GZIP",
    "brotli": "BROTLI",
}

FEATHER_CODECS = {
    "none": "uncompressed",
    "snappy": "zstd",  # Feather v2: map unsupported snappy -> zstd light
    "lz4": "lz4",
    "zstd": "zstd",
    "gzip": "zstd",  # Feather has no gzip; approximate with zstd
    "brotli": "zstd",
}


def parquet_compression(codec: str) -> str:
    return PARQUET_CODECS.get(codec.lower(), "SNAPPY")


def feather_compression(codec: str) -> str:
    return FEATHER_CODECS.get(codec.lower(), "zstd")


def codec_label(codec: str, level: int | None = None) -> str:
    c = codec.lower()
    if c == "zstd" and level is not None:
        return f"zstd-{level}"
    return c


def describe_codec(codec: str) -> dict[str, Any]:
    table = {
        "none": {
            "ratio": "1.0",
            "decode": "N/A",
            "regime": "Uncompressed baseline — max disk I/O",
        },
        "snappy": {
            "ratio": "Low",
            "decode": "Very fast",
            "regime": "CPU-friendly / speed path",
        },
        "lz4": {
            "ratio": "Low",
            "decode": "Very fast",
            "regime": "CPU-friendly / speed path",
        },
        "zstd": {
            "ratio": "Med–high (levels 1–22)",
            "decode": "Tunable",
            "regime": "Best balance — star of this case study",
        },
        "gzip": {
            "ratio": "High",
            "decode": "Slow",
            "regime": "Disk-bound / archival",
        },
        "brotli": {
            "ratio": "Highest",
            "decode": "Slowest",
            "regime": "Long-term storage",
        },
    }
    return table.get(codec.lower(), table["none"])
