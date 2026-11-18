"""Cross-Domain Intelligence Engine.

Connects environmental/civic complaints with voluntary symptom reports to
surface *potential community health concerns* worth investigating.

Method (all explainable, no black boxes):
1. Embed complaints + reports; filter candidate pairs by spatial proximity
   (<= MAX_ASSOCIATION_KM) and temporal proximity (<= MAX_ASSOCIATION_DAYS).
2. Score each pair with a weighted, auditable blend:
       association = w_sem * semantic_similarity
                   + w_spat * spatial_proximity(1 - d/km)
                   + w_temp * temporal_proximity(1 - t/days)
                   + w_theme * environmental->symptom theme match
   Theme weights encode that certain environmental complaints (e.g. water
   contamination) plausibly co-occur with certain symptom categories (e.g.
   gastrointestinal) — a co-occurrence prior, NOT causation.
3. Group high-scoring pairs into candidate clusters (connected components).
4. Run temporal anomaly detection on daily counts per district/category.
5. Emit alert candidates with full per-pair evidence breakdowns.

DISCLAIMER (enforced by the DISCLAIMER constant in ml/config.py):
association != causation, and scores are not clinical risk probabilities.
Alerts are investigation triggers for qualified officials only.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import numpy as np

from ml.anomaly.temporal import anomaly_alerts
from ml.clustering.clusterer import cluster_documents
from ml.config import DISCLAIMER, config
from ml.embeddings.embedder import cosine
from ml.preprocessing.gazetteer import haversine_km
from ml.preprocessing.lexicons import ENV_TO_HEALTH_THEME

logger = logging.getLogger(__name__)

ALERT_TYPES = {
    "CROSS_DOMAIN_CLUSTER": "Environmental complaints co-occurring with symptom reports in space and time",
    "TEMPORAL_ANOMALY": "Unusual increase in reporting volume",
    "SPATIAL_CLUSTER": "Concentration of similar complaints in one area",
}


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class CrossDomainEngine:
    """Stateless scan over records supplied by the caller (DB-agnostic)."""

    def __init__(self, embedder=None) -> None:
        self._embedder = embedder

    # ------------------------------------------------------------------ #
    # records                                                             #
    # ------------------------------------------------------------------ #
    def _prep(self, rows: list[dict], kind: str) -> list[dict]:
        """Normalize DB rows; compute embeddings when absent."""
        out = []
        for row in rows:
            rec = dict(row)
            rec["kind"] = kind
            text = rec.get("text") or rec.get("description") or ""
            rec["text"] = text
            if rec.get("embedding") is None and text:
                if self._embedder is None:
                    from ml.embeddings.embedder import get_embedder

                    self._embedder = get_embedder()
                rec["embedding"] = np.asarray(
                    self._embedder.encode_one(text), dtype=np.float32)
            elif rec.get("embedding") is not None:
                rec["embedding"] = np.asarray(rec["embedding"], dtype=np.float32)
            if isinstance(rec.get("created_at"), datetime):
                rec["created_at"] = _ensure_utc(rec["created_at"])
            rec.setdefault("symptom_categories", [])
            out.append(rec)
        return out

    # ------------------------------------------------------------------ #
    # pair scoring                                                        #
    # ------------------------------------------------------------------ #
    def _theme_match(self, complaint: dict, report: dict) -> float:
        """Fraction of the report's observed symptom categories that fall inside
        the environmental theme's plausible symptom space (co-occurrence prior,
        never causation)."""
        theme_cats = ENV_TO_HEALTH_THEME.get(complaint.get("category") or "", [])
        observed = report.get("symptom_categories") or []
        if not theme_cats or not observed:
            return 0.0
        overlap = set(theme_cats) & set(observed)
        if not overlap:
            return 0.0
        return min(1.0, len(overlap) / min(len(theme_cats), len(observed)))

    def _score_pair(self, complaint: dict, report: dict) -> dict | None:
        """Full evidence breakdown for one complaint/report pair."""
        if complaint.get("embedding") is None or report.get("embedding") is None:
            return None
        c_t = complaint.get("created_at")
        r_t = report.get("created_at")
        if not isinstance(c_t, datetime) or not isinstance(r_t, datetime):
            return None
        gap_days = abs((c_t - r_t).total_seconds()) / 86400.0
        if gap_days > config.max_association_days:
            return None

        lat_c, lng_c = complaint.get("lat"), complaint.get("lng")
        lat_r, lng_r = report.get("lat"), report.get("lng")
        if lat_c is None or lng_c is None or lat_r is None or lng_r is None:
            distance_km = None
            spatial = 0.0
        else:
            distance_km = haversine_km(lat_c, lng_c, lat_r, lng_r)
            if distance_km > config.max_association_km:
                return None
            spatial = max(0.0, 1.0 - distance_km / config.max_association_km)

        semantic = float(cosine(complaint["embedding"], report["embedding"]))
        temporal = max(0.0, 1.0 - gap_days / config.max_association_days)
        theme = self._theme_match(complaint, report)

        association = (
            config.w_semantic * semantic
            + config.w_spatial * spatial
            + config.w_temporal * temporal
            + config.w_theme * theme
        )
        return {
            "complaint_id": complaint.get("id"),
            "report_id": report.get("id"),
            "association_score": round(association, 4),
            "semantic_similarity": round(semantic, 4),
            "spatial_proximity": round(spatial, 4),
            "distance_km": round(distance_km, 3) if distance_km is not None else None,
            "temporal_proximity": round(temporal, 4),
            "gap_days": round(gap_days, 2),
            "theme_match": round(theme, 4),
            "complaint_category": complaint.get("category"),
            "district": complaint.get("district") or report.get("district"),
            "weights": {
                "semantic": config.w_semantic, "spatial": config.w_spatial,
                "temporal": config.w_temporal, "theme": config.w_theme,
            },
        }

    # ------------------------------------------------------------------ #
    # clustering of pairs into candidate clusters                          #
    # ------------------------------------------------------------------ #
    def _connected_components(self, pairs: list[dict]) -> list[set[str]]:
        parent: dict[str, str] = {}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a: str, b: str) -> None:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[rb] = ra

        for p in pairs:
            cid, rid = f"c:{p['complaint_id']}", f"r:{p['report_id']}"
            parent.setdefault(cid, cid)
            parent.setdefault(rid, rid)
            union(cid, rid)
        groups: dict[str, set[str]] = {}
        for node in parent:
            groups.setdefault(find(node), set()).add(node)
        return list(groups.values())

    # ------------------------------------------------------------------ #
    # main scan                                                            #
    # ------------------------------------------------------------------ #
    def scan(self, complaints: list[dict], reports: list[dict],
             daily_series: list[dict] | None = None) -> dict:
        """Run the full scan.

        daily_series: optional [{"key": "district|category", "points":
        [(date_str, count), ...]}] for temporal anomaly detection.
        Returns {"alerts": [...], "stats": {...}}.
        """
        c_recs = self._prep(complaints, "complaint")
        r_recs = self._prep(reports, "report")

        pairs: list[dict] = []
        for complaint in c_recs:
            for report in r_recs:
                scored = self._score_pair(complaint, report)
                if scored and scored["association_score"] >= config.association_threshold:
                    pairs.append(scored)
        pairs.sort(key=lambda p: p["association_score"], reverse=True)

        alerts: list[dict] = []
        stats = {
            "complaints_scanned": len(c_recs),
            "reports_scanned": len(r_recs),
            "candidate_pairs": len(pairs),
            "threshold": config.association_threshold,
        }

        # --- cross-domain cluster alerts -------------------------------
        if pairs:
            components = self._connected_components(pairs)
            pair_by_complaint: dict = {}
            for p in pairs:
                pair_by_complaint.setdefault(p["complaint_id"], p)
            complaints_by_id = {c["id"]: c for c in c_recs if c.get("id") is not None}
            reports_by_id = {r["id"]: r for r in r_recs if r.get("id") is not None}

            for component in components:
                complaint_ids = {n[2:] for n in component if n.startswith("c:")}
                report_ids = {n[2:] for n in component if n.startswith("r:")}
                comp_pairs = [p for p in pairs
                              if str(p["complaint_id"]) in complaint_ids
                              and str(p["report_id"]) in report_ids]
                if not comp_pairs:
                    continue
                mean_score = float(np.mean([p["association_score"] for p in comp_pairs]))
                top_pairs = sorted(comp_pairs, key=lambda p: p["association_score"], reverse=True)[:8]

                districts = sorted({
                    p["district"] for p in comp_pairs if p.get("district")
                })
                cats = sorted({
                    p["complaint_category"] for p in comp_pairs if p.get("complaint_category")
                })
                title = (
                    f"Cross-domain signal: {', '.join(cats[:2])} complaints near "
                    f"{', '.join(districts[:2])} overlap with symptom reports"
                )
                evidence: list[dict] = []
                for p in top_pairs:
                    c_rec = complaints_by_id.get(str(p["complaint_id"]),
                                                 complaints_by_id.get(p["complaint_id"]))
                    r_rec = reports_by_id.get(str(p["report_id"]),
                                              reports_by_id.get(p["report_id"]))
                    evidence.append({
                        "kind": "pair",
                        **p,
                        "complaint_excerpt": (c_rec or {}).get("text", "")[:180],
                        "report_symptoms": (r_rec or {}).get("symptoms", [])[:6],
                    })

                alerts.append({
                    "type": "CROSS_DOMAIN_CLUSTER",
                    "title": title,
                    "score": round(mean_score, 4),
                    "districts": districts,
                    "complaint_categories": cats,
                    "n_complaints": len(complaint_ids),
                    "n_reports": len(report_ids),
                    "n_supporting_pairs": len(comp_pairs),
                    "evidence": evidence,
                    "interpretation": (
                        "Statistical co-occurrence of environmental complaints and "
                        "symptom reports within space/time windows. This is an "
                        "investigation lead only — it does not establish causation "
                        "or a diagnosis."
                    ),
                })

        # --- temporal anomaly alerts ------------------------------------
        if daily_series:
            series_map: dict[str, list[tuple[str, int]]] = {}
            for entry in daily_series:
                series_map.setdefault(entry["key"], []).extend(
                    [(d, c) for d, c in entry["points"]])
            for key, points in series_map.items():
                points.sort()
                found = anomaly_alerts([p[0] for p in points], [p[1] for p in points], key)
                for f in found:
                    alerts.append({
                        "type": "TEMPORAL_ANOMALY",
                        "title": f"Unusual increase in '{f['series']}' on {f['date']}",
                        "score": min(1.0, round(f["lift"] / 5.0, 4)),
                        "districts": [f["series"]],
                        "complaint_categories": [],
                        "n_complaints": f["observed"],
                        "n_reports": 0,
                        "n_supporting_pairs": 0,
                        "evidence": [
                            {"kind": "temporal", **f,
                             "interpretation": "Observed count vs trailing baseline "
                                               "(z-score + EWMA/CUSUM agreement)."},
                        ],
                        "interpretation": (
                            "Reporting volume rose abnormally versus its trailing "
                            "baseline. Causes can include a real incident, a local "
                            "event, or reporting artifacts."
                        ),
                    })

        alerts.sort(key=lambda a: a["score"], reverse=True)
        stats["alerts_generated"] = len(alerts)
        return {"alerts": alerts, "stats": stats, "disclaimer": DISCLAIMER}
