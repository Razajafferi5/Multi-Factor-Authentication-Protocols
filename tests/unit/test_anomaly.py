"""Tests for the AI anomaly layer: feature extraction + scoring + explainer."""

from datetime import datetime, timedelta, timezone

from backend.models import AuthEvent
from backend.services.anomaly import explain_event, extract_features, score_event


def _event(ts, success=True, lat=None, lon=None, fp="device-a"):
    e = AuthEvent(
        user_id=1, factor="totp", success=success, device_fingerprint=fp, timestamp=ts
    )
    if lat is not None:
        e.set_geo({"lat": lat, "lon": lon, "city": "x", "country": "x"})
    return e


def test_impossible_travel_feature():
    now = datetime.now(timezone.utc)
    # Previous login in London 5 minutes ago...
    history = [_event(now - timedelta(minutes=5), lat=51.5074, lon=-0.1278)]
    # ...current login in Tokyo -> impossible travel.
    current = _event(now, lat=35.6762, lon=139.6503)
    features = extract_features(current, history)
    assert features["impossible_travel"] == 1.0
    assert features["geo_distance_km"] > 8000


def test_new_device_feature():
    now = datetime.now(timezone.utc)
    history = [_event(now - timedelta(days=1), fp="known-device")]
    current = _event(now, fp="brand-new-device")
    features = extract_features(current, history)
    assert features["new_device"] == 1.0


def test_failed_burst_feature():
    now = datetime.now(timezone.utc)
    history = [_event(now - timedelta(minutes=2), success=False) for _ in range(3)]
    current = _event(now)
    features = extract_features(current, history)
    assert features["failed_burst"] == 3.0


def test_scoring_cold_start_flags_obvious_anomaly():
    # With little history the rule-based fallback should flag impossible travel.
    features = {
        "geo_distance_km": 9000, "velocity_kmh": 5000, "impossible_travel": 1.0,
        "new_device": 1.0, "unusual_hour": 0.0, "failed_burst": 0.0,
    }
    score, flagged = score_event(features, history_features=[])
    assert flagged is True


def test_explainer_graceful_degradation_without_key():
    # conftest forces ANTHROPIC_API_KEY="" so this must use the fallback text.
    features = {
        "geo_distance_km": 9000, "velocity_kmh": 5000, "impossible_travel": 1.0,
        "new_device": 1.0, "unusual_hour": 0.0, "failed_burst": 0.0,
    }
    llm_text, display = explain_event(features, score=-0.4)
    assert llm_text is None  # no LLM call succeeded
    assert "impossible travel" in display.lower()
    assert "raw features" in display.lower()
