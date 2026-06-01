"""Authentication-event logging + anomaly scoring orchestration.

Every authentication attempt funnels through :func:`log_auth_event`, which:

1. Persists an ``AuthEvent`` row (the audit trail).
2. Extracts anomaly features from the user's history.
3. Scores the event with the IsolationForest detector.
4. For flagged events, asks the LLM explainer for a risk note (with graceful
   fallback to a feature summary).

This single choke-point guarantees the audit log and the AI layer never drift
apart - the log *is* the training data.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import AuthEvent
from ..utils.fingerprint import RequestContext
from .anomaly import explain_event, extract_features, score_event

# Only run the (relatively expensive) anomaly pipeline for these factors. Push
# poll endpoints, for instance, generate noise we don't want to score.
_SCORED_FACTORS = {"password", "totp", "hotp", "webauthn", "push", "backup_code"}


def _user_history(session: Session, user_id: int | None, before_id: int) -> list[AuthEvent]:
    """Return a user's prior events (excluding the current one)."""
    if user_id is None:
        return []
    stmt = (
        select(AuthEvent)
        .where(AuthEvent.user_id == user_id, AuthEvent.id != before_id)
        .order_by(AuthEvent.timestamp.asc())
    )
    return list(session.scalars(stmt))


def log_auth_event(
    session: Session,
    *,
    factor: str,
    success: bool,
    user_id: int | None = None,
    username_attempted: str | None = None,
    reason: str | None = None,
    context: RequestContext | None = None,
    run_anomaly: bool = True,
    occurred_at=None,
) -> AuthEvent:
    """Record one authentication attempt and (optionally) score it.

    Returns the persisted :class:`AuthEvent` (with anomaly fields populated when
    scoring ran). The caller is responsible for the surrounding transaction
    boundary, but this function commits so the event id is available.

    ``occurred_at`` overrides the event timestamp; it is used by the seed
    script so historical events are scored against their true time (rather than
    "now"), which keeps the velocity/impossible-travel features meaningful.
    """
    event = AuthEvent(
        user_id=user_id,
        username_attempted=username_attempted,
        factor=factor,
        success=success,
        reason=reason,
    )
    if occurred_at is not None:
        event.timestamp = occurred_at
    if context is not None:
        event.ip_address = context.ip_address
        event.device_fingerprint = context.device_fingerprint()
        event.user_agent = context.user_agent
        event.set_geo(context.geo())

    session.add(event)
    session.commit()  # assigns event.id

    if run_anomaly and factor in _SCORED_FACTORS and user_id is not None:
        _score_and_explain(session, event)

    return event


def _score_and_explain(session: Session, event: AuthEvent) -> None:
    """Run feature extraction, scoring and explanation for one event.

    ``history`` is ascending by timestamp and excludes the current event. To
    avoid leaking "future" information into a training sample's features, each
    historical event ``history[i]`` is featurised against only its own prior
    events ``history[:i]`` - the same temporal constraint used for the live
    event being scored.
    """
    history = _user_history(session, event.user_id, event.id)

    features = extract_features(event, history)
    event.set_features(features)

    history_features = [
        extract_features(history[i], history[:i]) for i in range(len(history))
    ]
    score, is_flagged = score_event(features, history_features)
    event.anomaly_score = score
    event.is_flagged = is_flagged

    if is_flagged:
        _llm_text, display = explain_event(features, score)
        event.explanation = display

    session.commit()


def list_events(
    session: Session,
    *,
    user_id: int | None = None,
    flagged_only: bool = False,
    limit: int = 500,
) -> list[AuthEvent]:
    """Query events for the dashboard / API, newest first."""
    stmt = select(AuthEvent).order_by(AuthEvent.timestamp.desc())
    if user_id is not None:
        stmt = stmt.where(AuthEvent.user_id == user_id)
    if flagged_only:
        stmt = stmt.where(AuthEvent.is_flagged.is_(True))
    stmt = stmt.limit(limit)
    return list(session.scalars(stmt))
