# Case Study 2: Balancing Compression Trade-Offs for High-Speed Data Processing

Web app + benchmarks that find the **CPU vs disk I/O balance** when storing and reading compressed columnar data on a single machine.

## Core idea

| Compression helps | Compression costs |
|-------------------|-------------------|
| Smaller files → less disk I/O, smaller footprint | CPU must decompress before use |

Goal: pick codec + level (especially **Zstd 1–22**) where I/O savings beat decode overhead.

## Requirements coverage

1. **Research trade-offs** — see below + [`docs/theory.md`](docs/theory.md)  
2. **Web UI** — configure codec/level/format; live CPU, disk-wait, throughput charts  
3. **Columnar compressed structures** — Parquet, Feather/Arrow, Blosc2, Zarr (Bcolz cited as legacy)  
4. **Data-path diagram** — [`docs/data_path.md`](docs/data_path.md)  
5. **Download + speedup test** — public CSV (with synthetic fallback); codec matrix vs uncompressed  

## Modern stack (not Bcolz)

Bcolz is deprecated. This project uses **Parquet**, **Arrow/Feather**, **Blosc2**, and **Zarr**.

## Codec spectrum

| Codec | Ratio | Decode | Regime |
|-------|-------|--------|--------|
| LZ4 / Snappy | Low | Very fast | CPU-friendly |
| **Zstd (1–22)** | Med–high | Tunable | Best balance — study star |
| Gzip | High | Slow | Disk-bound archival |
| Brotli | Highest | Slowest | Long-term storage |
| none | 1.0 | N/A | Uncompressed baseline |

## Quick start

```bash
cd Week-5
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000

1. **Download dataset**  
2. Set format/codec; drag **Zstd level 1–22**  
3. **Run ingest** or **Codec matrix** / **Zstd sweep** / **Full benchmark**  
4. Read the **recommendation** banner and balance-point chart  

## Presentation / បទបង្ហាញ

An 18-slide step-by-step deck is served at **http://127.0.0.1:8000/slides** — icons, illustrations, code blocks for each step, the balance-point graph, measured results, and the final recommendation. Navigate with ← → arrow keys, the dots, or swipe on touch devices.

## Khmer language / ភាសាខ្មែរ

Both the dashboard and the slides are bilingual. Click the **ខ្មែរ / English** button in the top-right to switch; the choice is remembered in the browser. Khmer text uses the Noto Sans Khmer font with wider line spacing for readability.

## Dataset source (R5)

The app downloads from public repositories in order: Titanic CSV → flight paths CSV → Pima diabetes CSV. These are small, so for measurable I/O vs CPU timing the app scales up to a synthetic taxi frame (~120k+ rows) while keeping the real download as proof of the online-repository step. If all URLs fail, it falls back fully to synthetic data so the demo works offline.

## Metrics collected

- Throughput (MB/s)  
- CPU utilization % during work  
- Disk I/O wait % (iowait or heuristic)  
- Peak RSS (MB)  
- Compression ratio = original ÷ compressed  

## Research findings (from local matrix run)

Sample run on this machine (`benchmarks/results.json`, ~20k synthetic taxi rows):

| Codec | Format | Ratio | Total (s) | Throughput MB/s | Notes |
|-------|--------|------:|----------:|----------------:|-------|
| none | CSV | 1.0× | 0.152 | 54 | Uncompressed baseline |
| snappy | Parquet | 1.84× | 0.073 | 22 | Fast write, moderate read |
| **lz4** | Parquet | 1.84× | **0.019** | **178** | Best wall-clock here |
| zstd L5 | Parquet | 2.05× | 0.024 | ~100+ | Strong balance of size + speed |
| gzip | Parquet | ~2.1× | slower than lz4/zstd | — | Higher ratio, more CPU |
| brotli | Parquet | highest | slowest decode | — | Archival / long-term store |

**Recommendation from the app:** on this SSD laptop, **lz4 (Parquet)** won the matrix (~8× vs uncompressed CSV total time) because decode is cheap and files are already small enough that extra gzip/brotli CPU does not pay off. Re-run **Full benchmark** / **Zstd sweep** on your disk — the winner can shift when I/O is slower (HDD/network) toward mid **zstd** levels.

Disk-wait stayed near 0% on this machine (fast SSD + warm cache), so the study often appears **CPU-bound**; on slower storage the balance-point chart should show disk-wait rising for `none`/low compression.

## Project layout

```
app/           FastAPI app, formats, ingest, metrics, benchmarks
docs/          Data path + theory
benchmarks/    results.json after runs
data/          downloaded + processed files (gitignored)
```

## API

- `POST /api/download`  
- `POST /api/ingest`  
- `POST /api/benchmark` `{ "mode": "full"|"matrix"|"zstd_sweep" }`  
- `GET /api/state` — live metrics  
- Interactive OpenAPI: http://127.0.0.1:8000/docs  
