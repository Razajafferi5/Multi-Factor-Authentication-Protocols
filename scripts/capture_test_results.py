"""Run the full test suite and capture REAL output to a timestamped file.

This produces the evidence artifact referenced in the project report. It runs
``pytest`` as a subprocess and writes the verbatim stdout/stderr plus the exit
code to ``test_evidence/report_<UTC timestamp>.txt``. Nothing is hand-edited -
the file is exactly what pytest printed.

Usage::

    python -m scripts.capture_test_results
"""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone

EVIDENCE_DIR = "test_evidence"


def main() -> int:
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(EVIDENCE_DIR, f"report_{stamp}.txt")

    cmd = [sys.executable, "-m", "pytest", "-v", "--tb=short"]
    print(f"Running: {' '.join(cmd)}")

    completed = subprocess.run(cmd, capture_output=True, text=True)
    output = completed.stdout + "\n" + completed.stderr

    header = (
        "MFA Authentication Server - Test Evidence\n"
        f"Captured (UTC): {datetime.now(timezone.utc).isoformat()}\n"
        f"Command: {' '.join(cmd)}\n"
        f"Exit code: {completed.returncode}\n"
        + "=" * 70 + "\n\n"
    )

    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(header)
        fh.write(output)

    print(output)
    print(f"\nEvidence written to: {out_path}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
