"""IsolationForest-based per-user anomaly scoring.

We train a fresh IsolationForest on the user's historical feature vectors and
score the new event against it. IsolationForest (Liu et al., 2008) isolates
anomalies with fewer random splits than normal points, making it well suited to
unlabelled login data where we have no ground-truth fraud labels.

Cold-start handling: with too few historical samples we cannot train a
meaningful model, so we fall back to a deterministic rule-based score derived
directly from the high-signal features (impossible travel, new device, failed
bursts). This keeps the system useful from the very first login.
"""

from __future__ import annotations

import numpy as np
from sklearn.ensemble import IsolationForest

from .features import FEATURE_ORDER, features_to_vector

# Minimum history required to train a per-user model.
MIN_TRAINING_SAMPLES = 8
# IsolationForest's contamination: expected fraction of anomalies. Kept low so
# the model only flags genuine outliers rather than normal day-to-day variation.
CONTAMINATION = 0.05
RANDOM_STATE = 42


def _rule_based_score(features: dict) -> tuple[float, bool]:
    """Deterministic fallback when there's not enough data to train a model.

    Returns ``(score, is_flagged)`` where ``score`` is in roughly [-1, 1] with
    lower meaning more anomalous, matching IsolationForest's convention.
    """
    risk = 0.0
    risk += 0.6 * features.get("impossible_travel", 0.0)
    risk += 0.3 * features.get("new_device", 0.0)
    risk += 0.2 * features.get("unusual_hour", 0.0)
    risk += 0.15 * min(features.get("failed_burst", 0.0), 5) / 5.0
    # Large geo jumps add a little risk even below the impossible-travel bar.
    if features.get("geo_distance_km", 0.0) > 2000:
        risk += 0.2
    risk = min(risk, 1.0)
    score = 1.0 - 2.0 * risk  # map risk[0,1] -> score[1,-1]
    is_flagged = risk >= 0.5
    return round(score, 4), is_flagged


def score_event(new_features: dict, history_features: list[dict]) -> tuple[float, bool]:
    """Score ``new_features`` given a list of historical feature dicts.

    Returns ``(anomaly_score, is_flagged)``. Higher score = more normal. An
    event is flagged when the model predicts it as an outlier (or, in fallback
    mode, when the rule-based risk crosses the threshold).
    """
    usable_history = [f for f in history_features if f]
    if len(usable_history) < MIN_TRAINING_SAMPLES:
        return _rule_based_score(new_features)

    train = np.array([features_to_vector(f) for f in usable_history], dtype=float)
    model = IsolationForest(
        n_estimators=100,
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
    )
    model.fit(train)

    x = np.array([features_to_vector(new_features)], dtype=float)
    # ``score_samples`` returns higher values for normal points.
    score = float(model.score_samples(x)[0])
    # ``predict`` returns -1 for anomalies, 1 for inliers.
    is_flagged = int(model.predict(x)[0]) == -1
    return round(score, 4), is_flagged
