"""Pick best codec/level from benchmark results and explain why."""
from __future__ import annotations

from typing import Any

from app.metrics import RunResult


def recommend_best(results: list[RunResult]) -> dict[str, Any]:
    valid = [r for r in results if r.total_seconds > 0 and r.compressed_bytes > 0]
    if not valid:
        return {
            "best_name": None,
            "message": "No successful runs yet. Run a benchmark first.",
            "score": None,
        }

    # Score: prioritize throughput and low total time; reward decent compression.
    def score(r: RunResult) -> float:
        # Higher is better
        thr = r.throughput_mb_s
        # Penalize very slow totals
        time_score = 1.0 / max(r.total_seconds, 1e-6)
        # Mild reward for compression ratio (log-ish via sqrt)
        ratio_bonus = (r.compression_ratio**0.5) * 0.15
        # Prefer not being extremely CPU-bound if disk wait is already low
        balance = 1.0 - abs(r.avg_cpu_percent - r.avg_disk_wait_percent) / 200.0
        return thr * 0.5 + time_score * 40.0 + ratio_bonus + balance

    ranked = sorted(valid, key=score, reverse=True)
    best = ranked[0]
    baseline = next((r for r in valid if r.codec == "none"), None)
    speedup = None
    if baseline and baseline.total_seconds > 0:
        speedup = round(baseline.total_seconds / best.total_seconds, 2)

    level_txt = f" level {best.level}" if best.codec == "zstd" and best.level else ""
    why_parts = [
        f"format={best.fmt}",
        f"throughput={best.throughput_mb_s} MB/s",
        f"ratio={best.compression_ratio}x",
        f"total={best.total_seconds}s",
        f"CPU≈{best.avg_cpu_percent}%",
        f"disk-wait≈{best.avg_disk_wait_percent}%",
    ]
    if speedup:
        why_parts.append(f"speedup_vs_uncompressed≈{speedup}x")

    message = (
        f"For this dataset on this machine, {best.codec}{level_txt} "
        f"({best.fmt}) is best because it balances I/O savings and decode cost "
        f"({'; '.join(why_parts)})."
    )
    return {
        "best_name": best.name,
        "codec": best.codec,
        "level": best.level,
        "fmt": best.fmt,
        "speedup_vs_uncompressed": speedup,
        "message": message,
        "score": round(score(best), 3),
        "top3": [
            {
                "name": r.name,
                "codec": r.codec,
                "level": r.level,
                "throughput_mb_s": r.throughput_mb_s,
                "total_seconds": r.total_seconds,
                "compression_ratio": r.compression_ratio,
            }
            for r in ranked[:3]
        ],
    }
