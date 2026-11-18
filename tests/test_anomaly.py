"""Temporal anomaly detection tests."""

from __future__ import annotations

from datetime import date, timedelta

from ml.anomaly.temporal import anomaly_alerts, detect_anomalies, detect_group_anomalies


def _series(base: int, spike_day: int, spike_value: int, days: int = 30) -> tuple[list[str], list[int]]:
    dates, counts = [], []
    start = date(2026, 10, 1)
    for i in range(days):
        dates.append((start + timedelta(days=i)).isoformat())
        counts.append(spike_value if i == spike_day else base)
    return dates, counts


class TestAnomalyDetection:
    def test_quiet_series_has_no_anomalies(self):
        dates, counts = _series(base=5, spike_day=-1, spike_value=5)
        signals = detect_anomalies(dates, counts)
        assert not any(s.is_anomaly for s in signals)

    def test_spike_detected(self):
        dates, counts = _series(base=5, spike_day=20, spike_value=30)
        alerts = anomaly_alerts(dates, counts, "Millbrook")
        assert alerts, "expected anomaly alert for the spike"
        top = alerts[0]
        assert top["date"] == dates[20]
        assert top["observed"] == 30
        assert top["lift"] >= 3.0
        assert top["methods"]  # explainable detector agreement

    def test_baseline_reported(self):
        dates, counts = _series(base=4, spike_day=10, spike_value=25)
        signals = detect_anomalies(dates, counts)
        spike = signals[10]
        assert spike.baseline_mean > 0
        assert spike.z > 2.0

    def test_group_anomalies_multi_series(self):
        dates_a, counts_a = _series(base=5, spike_day=15, spike_value=25)
        dates_b, counts_b = _series(base=6, spike_day=8, spike_value=8)  # no spike
        alerts = detect_group_anomalies({
            "Millbrook|water_contamination": list(zip(dates_a, counts_a)),
            "Northgate|noise": list(zip(dates_b, counts_b)),
        })
        assert any(a["series"].startswith("Millbrook") for a in alerts)
        assert all(not a["series"].startswith("Northgate") for a in alerts)

    def test_short_series_skipped(self):
        alerts = detect_group_anomalies({
            "Tiny": [("2026-10-01", 1), ("2026-10-02", 2)],
        })
        assert alerts == []
