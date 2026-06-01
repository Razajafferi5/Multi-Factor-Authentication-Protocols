"""AI anomaly-detection layer.

Pipeline:

1. ``features``  - turn an AuthEvent + the user's history into a numeric vector.
2. ``detector``  - score that vector with a per-user IsolationForest model.
3. ``explainer`` - ask Claude for a plain-language risk explanation, degrading
   gracefully to a feature summary if the LLM is unavailable.
"""

from .features import extract_features, FEATURE_ORDER
from .detector import score_event
from .explainer import explain_event

__all__ = ["extract_features", "FEATURE_ORDER", "score_event", "explain_event"]
