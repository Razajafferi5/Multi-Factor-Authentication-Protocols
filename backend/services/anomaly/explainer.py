"""LLM explainer: turn anomaly features into a plain-language risk note.

Given a flagged event's features and score, we ask Anthropic's Claude to write
a 2-3 sentence explanation an admin can read at a glance. The LLM ONLY explains
real output from the anomaly engine - it is not a free-form chatbot.

GRACEFUL DEGRADATION (a known viva question, handled explicitly here):
If the API key is missing, the SDK is unavailable, or the call errors/times
out, we DO NOT fail the login or the scoring. We return ``(None, fallback)``
where ``fallback`` is a deterministic human-readable summary of the raw
features, and the caller stores/show that instead of prose.
"""

from __future__ import annotations

from ...config import config

# Build a stable prompt so explanations are consistent and grounded only in the
# features we pass (no hallucinated context).
_SYSTEM_PROMPT = (
    "You are a security analyst assistant. You will be given the numeric "
    "anomaly features and score for a single login attempt that an anomaly "
    "detector has flagged. Write a concise 2-3 sentence explanation, for a "
    "security admin, of WHY this login looks risky, referring only to the "
    "provided features. Do not invent details. End with a short suggested "
    "action."
)


def _feature_summary(features: dict, score: float) -> str:
    """Deterministic, dependency-free fallback explanation."""
    bits = []
    if features.get("impossible_travel"):
        bits.append(
            f"impossible travel detected (~{features.get('velocity_kmh', 0):.0f} km/h "
            f"over {features.get('geo_distance_km', 0):.0f} km)"
        )
    elif features.get("geo_distance_km", 0) > 500:
        bits.append(f"login {features.get('geo_distance_km', 0):.0f} km from the previous location")
    if features.get("new_device"):
        bits.append("from a new/unrecognised device")
    if features.get("unusual_hour"):
        bits.append("at an unusual hour for this user")
    if features.get("failed_burst", 0) > 0:
        bits.append(f"following {int(features['failed_burst'])} recent failed attempt(s)")
    if not bits:
        bits.append("an unusual combination of login features")
    summary = "Flagged because of " + ", ".join(bits) + "."
    return f"{summary} (anomaly score {score:.3f}; LLM explanation unavailable - showing raw features.)"


def explain_event(features: dict, score: float) -> tuple[str | None, str]:
    """Return ``(llm_text_or_None, display_text)``.

    ``display_text`` is always populated: it is the LLM prose when available,
    otherwise the deterministic feature summary. ``llm_text_or_None`` lets the
    caller record whether the LLM actually produced the text (for the report).
    """
    fallback = _feature_summary(features, score)

    if not config.anthropic_api_key:
        # No key configured -> degrade gracefully, no network call attempted.
        return None, fallback

    try:
        # Imported lazily so a missing/old SDK can't break import-time.
        import anthropic

        client = anthropic.Anthropic(api_key=config.anthropic_api_key)
        user_content = (
            "Anomaly score (lower = more anomalous): "
            f"{score}\nFeatures:\n"
            + "\n".join(f"- {k}: {v}" for k, v in features.items())
        )
        message = client.messages.create(
            model=config.anthropic_model,
            max_tokens=200,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_content}],
        )
        # Concatenate any text blocks in the response.
        text = "".join(
            block.text for block in message.content if getattr(block, "type", None) == "text"
        ).strip()
        if not text:
            return None, fallback
        return text, text
    except Exception:  # noqa: BLE001 - any failure must degrade gracefully
        # Network error, auth error, rate limit, SDK mismatch, timeout, etc.
        return None, fallback
