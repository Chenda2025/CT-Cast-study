"""Shared paths and constants."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
BENCHMARKS_DIR = ROOT / "benchmarks"

# Public CSVs tried in order; synthetic taxi generated if all fail (offline demo).
DATASET_CANDIDATES = [
    (
        "https://raw.githubusercontent.com/datasciencedojo/datasets/master/titanic.csv",
        "titanic.csv",
    ),
    (
        "https://raw.githubusercontent.com/plotly/datasets/master/2011_february_aa_flight_paths.csv",
        "flight_paths.csv",
    ),
    (
        "https://raw.githubusercontent.com/jbrownlee/Datasets/master/pima-indians-diabetes.data.csv",
        "pima-diabetes.csv",
    ),
]
DEFAULT_DATASET_URL = DATASET_CANDIDATES[0][0]
DEFAULT_DATASET_NAME = DATASET_CANDIDATES[0][1]

CODECS = ["none", "snappy", "lz4", "zstd", "gzip", "brotli"]
FORMATS = ["parquet", "feather", "blosc2", "zarr", "csv"]
ZSTD_LEVELS = list(range(1, 23))
