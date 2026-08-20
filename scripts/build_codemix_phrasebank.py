"""
Codemix round 5, Stage 4 — assemble the FROZEN phrase bank
src/noisers/codemix.py reads at generation time, mirroring
build_codemix_wordbank.py's precedence-tier merge (same boundary between
offline/networked Stage A and deterministic/no-network Stage B -- see that
script's docstring).

Merges two sources into data/lexicon/codemix_phrasebank.jsonl, in
precedence order (earlier always overwrites later on a sinhala-phrase
conflict):
  1. LLM translations from codemix_phrase_translation_results.jsonl
     (scripts/translate_codemix_worklist.py --kind phrase), source="llm".
  2. data/lexicon/codemix_phrase_review_corrections.jsonl -- human
     corrections, same append-only "remove" / "correct" mechanism
     build_codemix_wordbank.py already uses for the word bank (a SEPARATE
     file from that one -- phrase corrections must never collide with word
     corrections on a coincidentally-shared key). Empty/absent until a
     human reviews the phrase bank the way codemix_usage_review.md drove
     word-bank round 4 -- the mechanism exists now so a future review round
     needs no new script, only new lines in this file.

Each row: {sinhala, words, n_words, english, source, codemix_plausible,
sold_frequency, evidence}. ALL translated entries are kept (not just
plausible ones), mirroring the word bank's own structure -- codemix_
plausible is a FLAG on every row, filtered at use time in
src/noisers/codemix.py, not a pre-filter here. This round explicitly keeps
the plausibility gate locked for both severities (no "eligible but not
plausible" phrase fallback tier was added -- see the plan's "Round 5"
section and docs/research_documentation.md for why), so in practice only
plausible=true rows are ever drawn from, but the frozen file itself stays
structurally parallel to the word bank for consistency and any future
reconsideration.

Run:  python scripts/build_codemix_phrasebank.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from _codemix_common import LEXICON_DIR, log

RESULTS_PATH = LEXICON_DIR / "codemix_phrase_translation_results.jsonl"
CORRECTIONS_PATH = LEXICON_DIR / "codemix_phrase_review_corrections.jsonl"
WORKLIST_PATH = LEXICON_DIR / "codemix_phrase_worklist.jsonl"
PHRASEBANK_PATH = LEXICON_DIR / "codemix_phrasebank.jsonl"
PHRASEBANK_HASH_PATH = LEXICON_DIR / ".codemix_phrasebank.sha256"


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    worklist_by_key = {row["sinhala"]: row for row in _load_jsonl(WORKLIST_PATH)}
    results = _load_jsonl(RESULTS_PATH)

    merged: dict[str, dict] = {}
    for row in results:
        sinhala = row["sinhala"]
        source_row = worklist_by_key.get(sinhala, {})
        merged[sinhala] = {
            "sinhala": sinhala,
            "words": source_row.get("words", sinhala.split(" ")),
            "n_words": source_row.get("n_words", len(sinhala.split(" "))),
            "english": row["english"],
            "source": "llm",
            "codemix_plausible": row["codemix_plausible"],
            "sold_frequency": row.get("sold_frequency", 0),
            "evidence": row.get("evidence", ""),
        }
    n_llm = len(merged)

    corrections = _load_jsonl(CORRECTIONS_PATH)
    n_corrected = n_removed = 0
    for row in corrections:
        sinhala = row["sinhala"]
        if row["action"] == "remove":
            if merged.pop(sinhala, None) is not None:
                n_removed += 1
            continue
        if row["action"] == "correct":
            prior = merged.get(sinhala, {})
            source_row = worklist_by_key.get(sinhala, {})
            merged[sinhala] = {
                "sinhala": sinhala,
                "words": source_row.get("words", sinhala.split(" ")),
                "n_words": source_row.get("n_words", len(sinhala.split(" "))),
                "english": row["english"],
                "source": "human_corrected",
                "codemix_plausible": row.get("codemix_plausible", True),
                "sold_frequency": prior.get("sold_frequency", 0),
                "evidence": row.get("note", ""),
            }
            n_corrected += 1
            continue
        raise ValueError(f"unknown correction action {row['action']!r} for {sinhala!r}")

    rows = sorted(merged.values(), key=lambda r: (-r["sold_frequency"], r["sinhala"]))
    n_plausible = sum(1 for r in rows if r["codemix_plausible"])

    log("build_phrasebank", f"{n_llm} llm-translated phrases loaded")
    if corrections:
        log("build_phrasebank", f"applied {len(corrections)} review corrections: "
            f"{n_corrected} corrected, {n_removed} removed")
    log("build_phrasebank", f"-> {len(rows)} unique phrase entries "
        f"({n_plausible} codemix_plausible=true)")

    with PHRASEBANK_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    digest = hashlib.sha256(PHRASEBANK_PATH.read_bytes()).hexdigest()
    PHRASEBANK_HASH_PATH.write_text(digest, encoding="utf-8")
    log("build_phrasebank", f"wrote {len(rows)} rows -> {PHRASEBANK_PATH}")
    log("build_phrasebank", f"sha256={digest} (first 8: {digest[:8]}) -> {PHRASEBANK_HASH_PATH}")


if __name__ == "__main__":
    main()
