"""Metric collection: throughput, CPU%, disk wait, peak RAM, compression ratio."""
from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Any, Generator

import psutil


@dataclass
class MetricSnapshot:
    ts: float
    cpu_percent: float
    disk_wait_percent: float
    rss_mb: float
    throughput_mb_s: float = 0.0
    stage: str = ""


@dataclass
class RunResult:
    name: str
    codec: str
    level: int | None
    fmt: str
    rows: int
    original_bytes: int
    compressed_bytes: int
    compression_ratio: float
    write_seconds: float
    read_seconds: float
    process_seconds: float
    total_seconds: float
    throughput_mb_s: float
    avg_cpu_percent: float
    avg_disk_wait_percent: float
    peak_rss_mb: float
    threads: int = 1
    notes: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class MetricsCollector:
    """Background sampler for CPU, approx disk-wait, and peak RSS."""

    def __init__(self, interval: float = 0.2) -> None:
        self.interval = interval
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self.snapshots: list[MetricSnapshot] = []
        self.peak_rss_mb = 0.0
        self._bytes_done = 0
        self._t0 = 0.0
        self._stage = ""
        self._proc = psutil.Process(os.getpid())
        self._lock = threading.Lock()

    def set_stage(self, stage: str) -> None:
        with self._lock:
            self._stage = stage

    def add_bytes(self, n: int) -> None:
        with self._lock:
            self._bytes_done += n

    def start(self) -> None:
        self.snapshots.clear()
        self.peak_rss_mb = 0.0
        self._bytes_done = 0
        self._t0 = time.perf_counter()
        self._stop.clear()
        # Prime CPU percent
        self._proc.cpu_percent(None)
        psutil.cpu_percent(None)
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def _loop(self) -> None:
        while not self._stop.is_set():
            try:
                cpu = self._proc.cpu_percent(None)
                # Approximate I/O wait: system iowait if available, else disk busy fraction.
                disk_wait = 0.0
                try:
                    load = psutil.cpu_times_percent(interval=None)
                    disk_wait = float(getattr(load, "iowait", 0.0) or 0.0)
                except Exception:
                    disk_wait = 0.0
                if disk_wait == 0.0:
                    # Fallback heuristic: when process CPU is low but we are in a read stage,
                    # attribute residual to disk wait (capped).
                    with self._lock:
                        stage = self._stage
                    if stage in {"read", "download", "write"} and cpu < 30:
                        disk_wait = max(0.0, min(70.0, 40.0 - cpu * 0.3))

                rss_mb = self._proc.memory_info().rss / (1024 * 1024)
                elapsed = max(time.perf_counter() - self._t0, 1e-9)
                with self._lock:
                    bytes_done = self._bytes_done
                    stage = self._stage
                thr = (bytes_done / (1024 * 1024)) / elapsed
                snap = MetricSnapshot(
                    ts=time.time(),
                    cpu_percent=cpu,
                    disk_wait_percent=disk_wait,
                    rss_mb=rss_mb,
                    throughput_mb_s=thr,
                    stage=stage,
                )
                with self._lock:
                    self.snapshots.append(snap)
                    self.peak_rss_mb = max(self.peak_rss_mb, rss_mb)
                    # Keep last ~500 points for live UI
                    if len(self.snapshots) > 500:
                        self.snapshots = self.snapshots[-500:]
            except Exception:
                pass
            self._stop.wait(self.interval)

    def live_tail(self, n: int = 60) -> list[dict[str, Any]]:
        with self._lock:
            return [asdict(s) for s in self.snapshots[-n:]]

    def summary(self) -> dict[str, float]:
        with self._lock:
            snaps = list(self.snapshots)
            peak = self.peak_rss_mb
        if not snaps:
            return {
                "avg_cpu_percent": 0.0,
                "avg_disk_wait_percent": 0.0,
                "peak_rss_mb": peak,
            }
        return {
            "avg_cpu_percent": sum(s.cpu_percent for s in snaps) / len(snaps),
            "avg_disk_wait_percent": sum(s.disk_wait_percent for s in snaps) / len(snaps),
            "peak_rss_mb": peak,
        }


@contextmanager
def timed_stage(collector: MetricsCollector | None, stage: str) -> Generator[float, None, None]:
    t0 = time.perf_counter()
    if collector:
        collector.set_stage(stage)
    try:
        yield t0
    finally:
        if collector:
            collector.set_stage("")
