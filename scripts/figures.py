"""Generate the figures embedded in the technical report.

Produces two kinds of images into ``docs/figures/``:

1. Schematic diagrams drawn deterministically with matplotlib patches
   (architecture, data flow, STRIDE threat model). Drawing them in code keeps
   them reproducible and consistent with the report text.
2. Data charts computed from the seeded database (logins over time,
   success/fail ratio, attempts by factor, anomaly-score distribution, and a
   login-location map). These are REAL metrics from the system, not mock-ups.

Run after seeding::

    python -m scripts.seed
    python -m scripts.figures
"""

from __future__ import annotations

import os
from collections import Counter
from datetime import timezone

import matplotlib

matplotlib.use("Agg")  # headless backend; no display needed.
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

FIG_DIR = os.path.join("docs", "figures")


def _ensure_dir() -> None:
    os.makedirs(FIG_DIR, exist_ok=True)


def _save(fig, name: str) -> str:
    path = os.path.join(FIG_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Schematic diagrams
# ---------------------------------------------------------------------------
def _box(ax, x, y, w, h, text):
    ax.add_patch(
        FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.02", linewidth=1.4,
            edgecolor="#33415c", facecolor="#dbe4ff",
        )
    )
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, wrap=True)


def _arrow(ax, x1, y1, x2, y2, label=None):
    ax.add_patch(
        FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14,
            linewidth=1.2, color="#33415c",
        )
    )
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 0.15, label, ha="center", fontsize=8)


def architecture_diagram() -> str:
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 8)
    ax.axis("off")

    _box(ax, 0.5, 6, 3, 1.2, "Streamlit Admin\nDashboard")
    _box(ax, 6.5, 6, 3, 1.2, "pytest /\nAPI clients")
    _box(ax, 3.2, 3.8, 3.6, 1.2, "Flask REST API\n(routes / blueprints)")
    _box(ax, 0.3, 1.4, 3, 1.4, "Crypto core\nHOTP / TOTP / AES-GCM\nArgon2id")
    _box(ax, 3.6, 1.4, 2.8, 1.4, "Services\nmfa / auth / push\nwebauthn / lockout")
    _box(ax, 6.7, 1.4, 3, 1.4, "AI anomaly layer\nfeatures / IForest / LLM")
    _box(ax, 3.6, 0.1, 2.8, 0.9, "SQLite (SQLAlchemy)")

    _arrow(ax, 2.0, 6.0, 4.2, 5.0, "HTTP")
    _arrow(ax, 8.0, 6.0, 5.8, 5.0, "HTTP")
    _arrow(ax, 2.0, 6.0, 1.8, 2.8, "EMBEDDED")
    _arrow(ax, 5.0, 3.8, 5.0, 2.8)
    _arrow(ax, 5.0, 2.8, 1.8, 2.8)
    _arrow(ax, 5.0, 2.8, 8.2, 2.8)
    _arrow(ax, 5.0, 1.4, 5.0, 1.0)
    ax.set_title("Figure: System Architecture", fontsize=11)
    return _save(fig, "architecture.png")


def dataflow_diagram() -> str:
    fig, ax = plt.subplots(figsize=(8, 3.2))
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3)
    ax.axis("off")
    steps = [
        "Client\n(credentials\n+ OTP + geo)",
        "Flask route",
        "Service\n(verify factor)",
        "Crypto\n(HOTP/TOTP\nAES-GCM)",
        "AuthEvent\nlogged",
        "Anomaly\nscore + flag",
    ]
    x = 0.2
    centers = []
    for s in steps:
        _box(ax, x, 1.1, 1.7, 1.1, s)
        centers.append(x + 0.85)
        x += 2.0
    for i in range(len(centers) - 1):
        _arrow(ax, centers[i] + 0.85, 1.65, centers[i + 1] - 0.85, 1.65)
    ax.set_title("Figure: Authentication Data Flow", fontsize=11)
    return _save(fig, "dataflow.png")


def threat_model_diagram() -> str:
    """STRIDE categories mapped to the mitigations in this system."""
    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.axis("off")
    rows = [
        ("Spoofing", "Multi-factor (TOTP/HOTP/WebAuthn/push); Argon2id passwords"),
        ("Tampering", "AES-256-GCM AEAD on secrets; WebAuthn signature checks"),
        ("Repudiation", "Immutable AuthEvent audit log of every attempt"),
        ("Information disclosure", "Secrets encrypted at rest; no plaintext OTP seeds"),
        ("Denial of service", "Sliding-window lockout + CAPTCHA (per user and IP)"),
        ("Elevation of privilege", "Replay prevention; WebAuthn sign-count clone check"),
    ]
    y = 0.92
    ax.text(0.02, y + 0.05, "STRIDE category", fontsize=10, fontweight="bold", transform=ax.transAxes)
    ax.text(0.40, y + 0.05, "Mitigation in this system", fontsize=10, fontweight="bold", transform=ax.transAxes)
    for cat, mit in rows:
        y -= 0.15
        ax.text(0.02, y, cat, fontsize=9, transform=ax.transAxes)
        ax.text(0.40, y, mit, fontsize=9, transform=ax.transAxes)
    ax.set_title("Figure: STRIDE Threat Model and Mitigations", fontsize=11)
    return _save(fig, "threat_model.png")


# ---------------------------------------------------------------------------
# Data charts from the seeded database
# ---------------------------------------------------------------------------
def _load_events():
    from backend.extensions import SessionLocal, init_db
    from backend.services.events import list_events

    init_db()
    s = SessionLocal()
    try:
        return [e.to_dict() for e in list_events(s, limit=100000)]
    finally:
        SessionLocal.remove()


def data_charts(events: list[dict]) -> list[str]:
    paths = []

    # 1) Attempts over time (by day).
    by_day: Counter = Counter()
    for e in events:
        ts = e.get("timestamp")
        if ts:
            by_day[ts[:10]] += 1
    if by_day:
        days = sorted(by_day)
        fig, ax = plt.subplots(figsize=(7, 3))
        ax.plot(days, [by_day[d] for d in days], marker="o")
        ax.set_title("Figure: MFA Attempts Over Time")
        ax.set_xlabel("Date")
        ax.set_ylabel("Attempts")
        ax.tick_params(axis="x", rotation=45, labelsize=7)
        paths.append(_save(fig, "attempts_over_time.png"))

    # 2) Success / failure ratio.
    successes = sum(1 for e in events if e.get("success"))
    failures = len(events) - successes
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie([successes, failures], labels=["success", "failure"], autopct="%1.0f%%",
           colors=["#4f8bf9", "#e06666"])
    ax.set_title("Figure: Success / Failure Ratio")
    paths.append(_save(fig, "success_fail_ratio.png"))

    # 3) Attempts by factor.
    by_factor = Counter(e.get("factor") for e in events)
    if by_factor:
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(list(by_factor.keys()), list(by_factor.values()), color="#4f8bf9")
        ax.set_title("Figure: Attempts by Factor")
        ax.set_ylabel("Count")
        paths.append(_save(fig, "attempts_by_factor.png"))

    # 4) Anomaly-score distribution (flagged vs normal).
    scores = [e["anomaly_score"] for e in events if e.get("anomaly_score") is not None]
    if scores:
        flagged = [e["anomaly_score"] for e in events
                   if e.get("anomaly_score") is not None and e.get("is_flagged")]
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.hist(scores, bins=20, color="#4f8bf9", alpha=0.7, label="all events")
        if flagged:
            ax.hist(flagged, bins=20, color="#e06666", alpha=0.8, label="flagged")
        ax.set_title("Figure: Anomaly Score Distribution")
        ax.set_xlabel("IsolationForest score (lower = more anomalous)")
        ax.set_ylabel("Frequency")
        ax.legend(fontsize=8)
        paths.append(_save(fig, "anomaly_scores.png"))

    # 5) Login-location map (simple lat/lon scatter on a world outline).
    coords = []
    for e in events:
        geo = e.get("geo")
        if isinstance(geo, dict) and geo.get("lat") is not None:
            coords.append((geo["lon"], geo["lat"], bool(e.get("is_flagged"))))
    if coords:
        fig, ax = plt.subplots(figsize=(7, 3.6))
        normal = [(x, y) for x, y, f in coords if not f]
        flag = [(x, y) for x, y, f in coords if f]
        if normal:
            ax.scatter([x for x, _ in normal], [y for _, y in normal],
                       c="#4f8bf9", s=25, label="normal")
        if flag:
            ax.scatter([x for x, _ in flag], [y for _, y in flag],
                       c="#e06666", s=45, marker="X", label="flagged")
        ax.set_xlim(-180, 180)
        ax.set_ylim(-90, 90)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title("Figure: Login Locations (flagged highlighted)")
        ax.grid(True, linewidth=0.3, alpha=0.5)
        ax.legend(fontsize=8)
        paths.append(_save(fig, "login_map.png"))

    return paths


def generate_all() -> list[str]:
    _ensure_dir()
    paths = [
        architecture_diagram(),
        dataflow_diagram(),
        threat_model_diagram(),
    ]
    events = _load_events()
    paths += data_charts(events)
    print(f"Generated {len(paths)} figures in {FIG_DIR}:")
    for p in paths:
        print(f"  {p}")
    return paths


if __name__ == "__main__":
    generate_all()
