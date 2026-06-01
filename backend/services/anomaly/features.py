"""Feature extraction for the anomaly engine.

Given a new (uncommitted or just-created) ``AuthEvent`` and the user's recent
history, produce a numeric feature vector that captures the signals security
teams care about for account-takeover detection:

* ``geo_distance_km``   - distance from the last successful login location.
* ``velocity_kmh``      - implied travel speed since the last login.
* ``impossible_travel`` - 1.0 if velocity exceeds a plausible air-travel speed.
* ``new_device``        - 1.0 if this device fingerprint is unseen recently.
* ``unusual_hour``      - 1.0 if the local hour is outside the user's norm.
* ``failed_burst``      - count of recent failed attempts (brute-force signal).

The feature ORDER is fixed so the matrix columns are stable across training and
scoring.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ...models import AuthEvent
from ...utils.geo import haversine_km, travel_velocity_kmh

# Stable column order for the model matrix.
FEATURE_ORDER = [
    "geo_distance_km",
    "velocity_kmh",
    "impossible_travel",
    "new_device",
    "unusual_hour",
    "failed_burst",
]

# A jet cruises at ~900 km/h; anything faster than this between two logins is
# physically implausible and a classic impossible-travel indicator.
IMPOSSIBLE_TRAVEL_KMH = 900.0
NEW_DEVICE_WINDOW_DAYS = 30
FAILED_BURST_WINDOW_MINUTES = 15


def _aware(dt: datetime) -> datetime:
    """Coerce a possibly-naive SQLite timestamp into UTC-aware."""
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def extract_features(event: AuthEvent, history: list[AuthEvent]) -> dict:
    """Compute the feature dict for ``event`` given prior ``history``.

    ``history`` should be the user's events strictly *before* ``event``,
    most-recent first is not required (we sort internally). All features
    degrade sensibly when there is little or no history (cold start).
    """
    now = _aware(event.timestamp)
    geo = event.get_geo()

    # Most recent successful login with a known location, before this event.
    last_geo_event = None
    for past in sorted(history, key=lambda e: e.timestamp, reverse=True):
        if past.success and past.get_geo():
            last_geo_event = past
            break

    geo_distance_km = 0.0
    velocity_kmh = 0.0
    impossible_travel = 0.0
    if geo and last_geo_event is not None:
        last_geo = last_geo_event.get_geo()
        geo_distance_km = haversine_km(
            geo["lat"], geo["lon"], last_geo["lat"], last_geo["lon"]
        )
        elapsed = (now - _aware(last_geo_event.timestamp)).total_seconds()
        velocity_kmh = travel_velocity_kmh(geo_distance_km, elapsed)
        impossible_travel = 1.0 if velocity_kmh > IMPOSSIBLE_TRAVEL_KMH else 0.0

    # New-device flag: fingerprint not seen in the recent window.
    new_device = 0.0
    if event.device_fingerprint:
        cutoff = now - timedelta(days=NEW_DEVICE_WINDOW_DAYS)
        seen = any(
            past.device_fingerprint == event.device_fingerprint
            and _aware(past.timestamp) >= cutoff
            for past in history
        )
        new_device = 0.0 if seen else 1.0

    # Unusual-hour flag: compare this event's hour to the user's historical
    # successful-login hours. With <5 prior logins we can't judge, so 0.
    unusual_hour = 0.0
    success_hours = [
        _aware(p.timestamp).hour for p in history if p.success
    ]
    if len(success_hours) >= 5:
        common_hours = set(success_hours)
        # Flag if the current hour is more than 3 hours from every common hour.
        if all(min((now.hour - h) % 24, (h - now.hour) % 24) > 3 for h in common_hours):
            unusual_hour = 1.0

    # Failed-burst: failures in the recent window before this event.
    burst_cutoff = now - timedelta(minutes=FAILED_BURST_WINDOW_MINUTES)
    failed_burst = float(
        sum(
            1
            for p in history
            if not p.success and _aware(p.timestamp) >= burst_cutoff
        )
    )

    return {
        "geo_distance_km": round(geo_distance_km, 3),
        "velocity_kmh": round(velocity_kmh, 3),
        "impossible_travel": impossible_travel,
        "new_device": new_device,
        "unusual_hour": unusual_hour,
        "failed_burst": failed_burst,
    }


def features_to_vector(features: dict) -> list[float]:
    """Project a feature dict onto the fixed ``FEATURE_ORDER`` vector."""
    return [float(features.get(name, 0.0)) for name in FEATURE_ORDER]
