# Theory notes — Amdahl, Roofline, and multi-threaded decompress

## Why decompression can become the new bottleneck

### Amdahl’s Law (intuition)
If a large fraction of end-to-end time was disk I/O, shrinking files speeds that fraction up. The remaining serial work — especially single-threaded decode — becomes a larger share of total time. After enough I/O improvement, **further compression helps little** unless decode itself gets faster (better codec or more threads).

### Roofline model (intuition)
Performance is limited by either:
- **Memory/disk bandwidth** (moving bytes), or
- **Compute** (decode + analytics flops)

Uncompressed CSV → often bandwidth-bound.  
Heavy gzip/brotli → often compute-bound.  
**Zstd mid levels / LZ4 / Snappy** sit near the “ridge” where both resources are used well — that ridge is the case study’s **balance point**.

## Multi-threaded decompression
Blosc2 and Zstd can split frames across cores. Raising thread count reduces wall-clock decode when the machine is CPU-bound on decompress, until memory bandwidth saturates.

This app’s **thread scaling** benchmark (Blosc2 + Zstd) demonstrates that effect.

## Bcolz → modern stack
Bcolz pioneered compressed columnar arrays in Python but is effectively unmaintained. Industry practice moved to:

| Legacy | Modern stand-in in this project |
|--------|----------------------------------|
| Bcolz carray | **Blosc2** NDArray / pack_array |
| Compressed columns on disk | **Parquet** + **Feather** |
| Chunked N-D scientific data | **Zarr** + numcodecs |

Comparing them shows awareness of real analytics stacks, not only the textbook name in the brief.
