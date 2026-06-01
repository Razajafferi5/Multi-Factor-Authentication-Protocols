"""Export the authentication-event log to a CSV dataset.

Satisfies the Phase 5 "dataset" deliverable. The exported file contains every
``AuthEvent`` row flattened to columns - including the extracted anomaly
features and the IsolationForest score - so the data behind the AI layer and
the report's Results section is reproducible and inspectable.

Usage::

    python -m scripts.export_dataset            # -> dataset/auth_events.csv
"""

from __future__ import annotations

import csv
import os

from backend.extensions import SessionLocal, init_db
from backend.services.anomaly.features import FEATURE_ORDER
from backend.services.events import list_events

OUTPUT_DIR = "dataset"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "auth_events.csv")


def export() -> str:
    init_db()
    session = SessionLocal()
    try:
        rows = list_events(session, limit=100000)
    finally:
        SessionLocal.remove()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base_cols = [
        "id", "user_id", "username_attempted", "factor", "success", "reason",
        "ip_address", "device_fingerprint", "timestamp",
        "geo_lat", "geo_lon", "geo_city", "geo_country",
        "anomaly_score", "is_flagged",
    ]
    feature_cols = [f"feat_{name}" for name in FEATURE_ORDER]
    header = base_cols + feature_cols

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        for ev in rows:
            d = ev.to_dict()
            geo = d.get("geo") or {}
            features = d.get("features") or {}
            row = [
                d["id"], d["user_id"], d["username_attempted"], d["factor"],
                d["success"], d["reason"], d["ip_address"], d["device_fingerprint"],
                d["timestamp"],
                geo.get("lat"), geo.get("lon"), geo.get("city"), geo.get("country"),
                d["anomaly_score"], d["is_flagged"],
            ]
            row += [features.get(name) for name in FEATURE_ORDER]
            writer.writerow(row)

    print(f"Exported {len(rows)} events to {OUTPUT_FILE}")
    return OUTPUT_FILE


if __name__ == "__main__":
    export()
