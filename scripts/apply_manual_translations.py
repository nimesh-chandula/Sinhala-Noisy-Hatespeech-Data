"""
Phase 3 density expansion, step 2c — merge scripts/codemix_manual_translations.py's
TRANSLATIONS and SKIP_NOTES into data/lexicon/codemix_candidates_review.csv.

Run:  python scripts/apply_manual_translations.py
Rewrites data/lexicon/codemix_candidates_review.csv in place.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.codemix_manual_translations import TRANSLATIONS, SKIP_NOTES  # noqa: E402

CSV_PATH = REPO_ROOT / "data" / "lexicon" / "codemix_candidates_review.csv"


def log(msg: str) -> None:
    print(f"[apply_manual_translations] {msg}")


def main() -> None:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    n_translated = n_skipped = 0
    unmatched_translations = set(TRANSLATIONS)
    unmatched_skips = set(SKIP_NOTES)

    for row in rows:
        word = row["sinhala"]
        if word in TRANSLATIONS:
            english, source, note = TRANSLATIONS[word]
            row["proposed_english"] = english
            row["confidence_note"] = f"reviewed ({source}): {note}"
            n_translated += 1
            unmatched_translations.discard(word)
        elif word in SKIP_NOTES:
            row["confidence_note"] = f"reviewed, skip: {SKIP_NOTES[word]}"
            n_skipped += 1
            unmatched_skips.discard(word)

    # Every row with sold_frequency >= FULLY_REVIEWED_FLOOR was actually
    # read and judged during the manual review batches (see LOG.md "Phase 3
    # density expansion") — most skip decisions relied on
    # classify_codemix_candidates.py's existing categories rather than a
    # bespoke note per word, so a leftover "needs_manual_review" tag in this
    # band is misleading (it reads as "not yet looked at", which is false).
    # Mark them explicitly reviewed instead.
    FULLY_REVIEWED_FLOOR = 9
    n_marked_reviewed = 0
    for row in rows:
        if (row["confidence_note"] == "needs_manual_review"
                and row["prior_status"] == "new"
                and int(row["sold_frequency"]) >= FULLY_REVIEWED_FLOOR):
            row["confidence_note"] = (
                "reviewed, skip: not a viable translation target "
                "(pronoun/particle/verb form/proper noun/low plausibility "
                "— not individually noted, see LOG.md 'Phase 3 density expansion')"
            )
            n_marked_reviewed += 1

    log(f"{n_translated} rows given a proposed translation")
    log(f"{n_skipped} rows given an individually-reviewed skip note")
    log(f"{n_marked_reviewed} more freq>={FULLY_REVIEWED_FLOOR} rows marked reviewed-but-not-viable "
        f"(genuinely looked at, no bespoke note written)")
    if unmatched_translations:
        log(f"WARNING: {len(unmatched_translations)} TRANSLATIONS entries matched no CSV row: {sorted(unmatched_translations)}")
    if unmatched_skips:
        log(f"WARNING: {len(unmatched_skips)} SKIP_NOTES entries matched no CSV row: {sorted(unmatched_skips)}")

    # utf-8-sig (BOM) so Excel/Google Sheets auto-detect UTF-8 and render
    # the Sinhala columns correctly instead of mojibake — this is the last
    # step before the file goes to the user for manual review.
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "sinhala", "sold_frequency", "prior_status",
            "proposed_english", "confidence_note", "accept", "final_english",
        ])
        writer.writeheader()
        writer.writerows(rows)
    log(f"rewrote {CSV_PATH}")


if __name__ == "__main__":
    main()
