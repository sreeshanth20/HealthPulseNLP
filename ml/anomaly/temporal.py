"""Temporal anomaly detection for report/complaint counts.

Three complementary detectors, all explainable and dependency-light:
- z-score against a trailing baseline window
- EWMA (exponentially weighted moving average) control limits
- Poisson CUSUM (cumulative sum of deviations from expected rate)

An anomaly verdict requires at least two methods to agree (reduces false
positives). Returns per-day diagnostics plus aggregated alert candidates.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from ml.config import config


@dataclass
class DaySignal:
    date: str
    value: int
    baseline_mean: float
    z: float
    ewma_upper: float
    cusum: float
    is_anomaly: bool
    methods: list[str]
    lift: float


def _zscore(series: list[int], i: int, window: int) -> tuple[float, float]:
    lo = max(0, i - window)
    baseline = series[lo:i]
    if len(baseline) < config.anomaly_min_history:
        return 0.0, float(sum(baseline)) if baseline else 0.0
    mean = sum(baseline) / len(baseline)
    var = sum((x - mean) ** 2 for x in baseline) / len(baseline)
    std = math.sqrt(var) or 1e-9
    return (series[i] - mean) / std, mean


def _ewma_limits(series: list[int], i: int, lam: float = 0.3, k: float = 2.5) -> tuple[float, float, float]:
    """Return (ewma_mean, upper_limit, baseline) up to index i."""
    lo = max(0, i - 14)
    base = series[lo:i] or [series[i]]
    mean0 = sum(base) / len(base)
    ewma = mean0
    for x in base:
        ewma = lam * x + (1 - lam) * ewma
    std = (math.sqrt(mean0) if mean0 > 0 else 1.0)  # Poisson-ish std
    return ewma, ewma + k * std / math.sqrt(lam / (2 - lam)) if mean0 > 0 else ewma, mean0


def detect_anomalies(dates: list[str], counts: list[int],
                     window: int = 14) -> list[DaySignal]:
    """Full per-day diagnostics; requires z-score AND (EWMA or CUSUM)."""
    signals: list[DaySignal] = []
    cusum = 0.0
    for i, (date, value) in enumerate(zip(dates, counts)):
        z, baseline = _zscore(counts, i, window)
        ewma, upper, mean0 = _ewma_limits(counts, i)
        expected = max(mean0, 0.5)
        cusum = max(0.0, cusum + (value - expected) / math.sqrt(max(expected, 1.0)) - 0.5)
        methods: list[str] = []
        if baseline and z >= config.anomaly_z_threshold:
            methods.append("zscore")
        if value > upper:
            methods.append("ewma")
        if cusum >= 5.0:
            methods.append("cusum")
        lift = value / expected if expected > 0 else 0.0
        is_anomaly = ("zscore" in methods and len(methods) >= 2) or (lift >= 3.0 and "zscore" in methods)
        signals.append(DaySignal(
            date=date, value=value, baseline_mean=round(baseline, 2), z=round(z, 2),
            ewma_upper=round(upper, 2), cusum=round(cusum, 2),
            is_anomaly=is_anomaly, methods=methods, lift=round(lift, 2),
        ))
    return signals


def anomaly_alerts(dates: list[str], counts: list[int], series_key: str,
                   window: int = 14) -> list[dict]:
    """Aggregated anomaly alert candidates for a named series."""
    out: list[dict] = []
    signals = detect_anomalies(dates, counts, window)
    for s in signals:
        if s.is_anomaly:
            out.append({
                "series": series_key,
                "date": s.date,
                "observed": s.value,
                "expected": s.baseline_mean,
                "lift": s.lift,
                "methods": s.methods,
                "cusum": s.cusum,
            })
    return out


def detect_group_anomalies(series: dict[str, list[tuple[str, int]]],
                           window: int = 14) -> list[dict]:
    """Run anomaly detection over many series (e.g. district x category)."""
    alerts: list[dict] = []
    for key, points in series.items():
        if len(points) < config.anomaly_min_history + 1:
            continue
        dates = [p[0] for p in points]
        counts = [p[1] for p in points]
        alerts.extend(anomaly_alerts(dates, counts, key, window))
    alerts.sort(key=lambda a: a["lift"], reverse=True)
    return alerts
