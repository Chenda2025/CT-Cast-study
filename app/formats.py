"""Columnar / compressed format writers and readers (Parquet, Feather, Blosc2, Zarr, CSV)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.feather as feather
import pyarrow.parquet as pq

from app.codecs import feather_compression, parquet_compression


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_parquet(
    df: pd.DataFrame,
    path: Path,
    codec: str = "snappy",
    level: int | None = None,
) -> int:
    ensure_parent(path)
    compression = parquet_compression(codec)
    kwargs: dict[str, Any] = {"compression": compression}
    if codec.lower() == "zstd" and level is not None:
        kwargs["compression_level"] = int(level)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, path, **kwargs)
    return path.stat().st_size


def read_parquet(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    return pq.read_table(path, columns=columns).to_pandas()


def write_feather(
    df: pd.DataFrame,
    path: Path,
    codec: str = "zstd",
    level: int | None = None,
) -> int:
    ensure_parent(path)
    compression = feather_compression(codec)
    # pyarrow feather compression_level only for zstd/lz4
    cl = int(level) if level is not None and compression in {"zstd", "lz4"} else None
    table = pa.Table.from_pandas(df, preserve_index=False)
    feather.write_feather(table, path, compression=compression, compression_level=cl)
    return path.stat().st_size


def read_feather(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    table = feather.read_table(path, columns=columns)
    return table.to_pandas()


def write_csv(df: pd.DataFrame, path: Path) -> int:
    ensure_parent(path)
    df.to_csv(path, index=False)
    return path.stat().st_size


def read_csv(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    return pd.read_csv(path, usecols=columns)


def write_blosc2(
    df: pd.DataFrame,
    path: Path,
    codec: str = "zstd",
    level: int | None = 5,
    threads: int = 4,
) -> int:
    """Store numeric columns as a Blosc2 NDArray container (columnar chunks)."""
    import blosc2

    ensure_parent(path)
    if path.exists():
        path.unlink()

    cmap = {
        "none": blosc2.Codec.BLOSCLZ,
        "snappy": blosc2.Codec.LZ4,
        "lz4": blosc2.Codec.LZ4,
        "zstd": blosc2.Codec.ZSTD,
        "gzip": blosc2.Codec.ZSTD,
        "brotli": blosc2.Codec.ZSTD,
    }
    cname = cmap.get(codec.lower(), blosc2.Codec.ZSTD)
    clevel = 0 if codec.lower() == "none" else int(level or 5)
    clevel = max(0, min(9, clevel if codec.lower() != "zstd" else min(9, (level or 5))))

    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        arr = np.arange(len(df), dtype=np.float64)
        meta_df = pd.DataFrame({"row": arr})
    else:
        arr = np.ascontiguousarray(numeric.to_numpy(dtype=np.float64, copy=True))
        meta_df = numeric.head(0)

    blosc2.set_nthreads(max(1, threads))
    cparams = {
        "codec": cname,
        "clevel": clevel,
        "nthreads": max(1, threads),
        "typesize": arr.dtype.itemsize,
    }
    blosc2.asarray(arr, urlpath=str(path), mode="w", cparams=cparams)
    meta = Path(str(path) + ".meta.csv")
    meta_df.to_csv(meta, index=False)
    return path.stat().st_size + (meta.stat().st_size if meta.exists() else 0)


def read_blosc2(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    import blosc2

    meta = Path(str(path) + ".meta.csv")
    arr = blosc2.open(str(path))[:]
    if meta.exists():
        cols = pd.read_csv(meta, nrows=0).columns.tolist()
        if arr.ndim == 1:
            df = pd.DataFrame({cols[0]: arr})
        else:
            use_cols = cols[: arr.shape[1]] if arr.ndim == 2 else cols
            df = pd.DataFrame(arr, columns=use_cols)
        if columns:
            keep = [c for c in columns if c in df.columns]
            return df[keep] if keep else df
        return df
    return pd.DataFrame(arr)


def write_zarr(
    df: pd.DataFrame,
    path: Path,
    codec: str = "zstd",
    level: int | None = 5,
) -> int:
    import numcodecs
    import zarr

    ensure_parent(path)
    if path.exists():
        import shutil

        shutil.rmtree(path)

    level = int(level or 5)
    if codec.lower() == "none":
        compressor = None
    elif codec.lower() == "lz4":
        compressor = numcodecs.LZ4()
    elif codec.lower() == "gzip":
        compressor = numcodecs.GZip(level=min(9, level))
    elif codec.lower() == "brotli":
        try:
            compressor = numcodecs.Brotli(clevel=min(11, level))
        except Exception:
            compressor = numcodecs.Zstd(level=level)
    elif codec.lower() == "snappy":
        try:
            compressor = numcodecs.Blosc(cname="lz4", clevel=5, shuffle=numcodecs.Blosc.SHUFFLE)
        except Exception:
            compressor = numcodecs.LZ4()
    else:  # zstd
        compressor = numcodecs.Zstd(level=max(1, min(22, level)))

    root = zarr.open_group(str(path), mode="w")
    numeric = df.select_dtypes(include=[np.number])
    total = 0
    if numeric.empty:
        data = np.arange(len(df), dtype=np.float64)
        root.create_dataset("values", data=data, compressor=compressor, overwrite=True)
    else:
        for col in numeric.columns:
            data = numeric[col].to_numpy()
            root.create_dataset(str(col), data=data, compressor=compressor, overwrite=True)
    # Measure directory size
    for p in path.rglob("*"):
        if p.is_file():
            total += p.stat().st_size
    return total


def read_zarr(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    import zarr

    root = zarr.open_group(str(path), mode="r")
    keys = list(root.array_keys())
    if columns:
        keys = [k for k in keys if k in columns] or keys
    data = {k: root[k][:] for k in keys}
    return pd.DataFrame(data)


def write_frame(
    df: pd.DataFrame,
    path: Path,
    fmt: str,
    codec: str = "snappy",
    level: int | None = None,
    threads: int = 4,
) -> int:
    fmt = fmt.lower()
    if fmt == "parquet":
        return write_parquet(df, path, codec=codec, level=level)
    if fmt == "feather":
        return write_feather(df, path, codec=codec, level=level)
    if fmt == "blosc2":
        return write_blosc2(df, path, codec=codec, level=level, threads=threads)
    if fmt == "zarr":
        return write_zarr(df, path, codec=codec, level=level)
    if fmt == "csv":
        return write_csv(df, path)
    raise ValueError(f"Unknown format: {fmt}")


def read_frame(path: Path, fmt: str, columns: list[str] | None = None) -> pd.DataFrame:
    fmt = fmt.lower()
    if fmt == "parquet":
        return read_parquet(path, columns=columns)
    if fmt == "feather":
        return read_feather(path, columns=columns)
    if fmt == "blosc2":
        return read_blosc2(path, columns=columns)
    if fmt == "zarr":
        return read_zarr(path, columns=columns)
    if fmt == "csv":
        return read_csv(path, columns=columns)
    raise ValueError(f"Unknown format: {fmt}")


def extension_for(fmt: str) -> str:
    return {
        "parquet": ".parquet",
        "feather": ".feather",
        "blosc2": ".b2nd",
        "zarr": ".zarr",
        "csv": ".csv",
    }.get(fmt.lower(), ".bin")
