"""
Code-mix bank correction, round 4 — Stage 1 (apply approved removals).

Reads the `decision` column of data/lexicon/codemix_removals_round4.csv (the
Stage 0 proposal from scripts/propose_codemix_removals.py, already reviewed:
Tier 1 affect-bearing and Tier 2 bare-verb entries approved for removal, Tier
3 left alone) and appends one {"sinhala", "action": "remove", "note"} row per
approved entry to data/lexicon/codemix_review_corrections.jsonl — the same
append-only correction file rounds 1-3 used, so this is round 4 by the
existing mechanism, not a new one. Then reruns build_codemix_wordbank.py so
the removal actually takes effect (corrections are the highest-precedence
tier there; see that script's docstring).

Idempotent: rows already appended by a prior run of this script (tagged
"round4" in their note) are not appended again.

Run:  python scripts/apply_codemix_removals.py
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEXICON_DIR = REPO_ROOT / "data" / "lexicon"
CSV_PATH = LEXICON_DIR / "codemix_removals_round4.csv"
CORRECTIONS_PATH = LEXICON_DIR / "codemix_review_corrections.jsonl"
BUILD_SCRIPT = Path(__file__).resolve().parent / "build_codemix_wordbank.py"


def main() -> None:
    if not CSV_PATH.exists():
        print(f"[apply_codemix_removals] {CSV_PATH} not found — run propose_codemix_removals.py first")
        return

    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    approved = [r for r in rows if r["decision"].strip().lower() == "remove"]
    print(f"[apply_codemix_removals] {len(approved)}/{len(rows)} rows marked decision=remove in {CSV_PATH.name}")

    already_removed: set[str] = set()
    if CORRECTIONS_PATH.exists():
        with CORRECTIONS_PATH.open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                if row.get("action") == "remove" and "round4" in row.get("note", ""):
                    already_removed.add(row["sinhala"])

    to_append = [r for r in approved if r["sinhala"] not in already_removed]
    skipped = len(approved) - len(to_append)
    if skipped:
        print(f"[apply_codemix_removals] {skipped} already appended by a prior run — skipping")

    if to_append:
        with CORRECTIONS_PATH.open("a", encoding="utf-8") as f:
            for r in to_append:
                note = f"round4 tier {r['tier']}: {r['reason']}"
                f.write(json.dumps({"sinhala": r["sinhala"], "action": "remove", "note": note}, ensure_ascii=False) + "\n")
        print(f"[apply_codemix_removals] appended {len(to_append)} removal rows -> {CORRECTIONS_PATH}")
    else:
        print("[apply_codemix_removals] nothing new to append")

    print("[apply_codemix_removals] rebuilding word bank...")
    result = subprocess.run([sys.executable, str(BUILD_SCRIPT)], cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print("[apply_codemix_removals] build_codemix_wordbank.py failed")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
