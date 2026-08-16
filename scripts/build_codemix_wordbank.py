"""
Phase 3 redesign, Stage A step 3 — assemble the FROZEN word bank the noiser
reads at generation time. This is the boundary between Stage A (offline,
networked, non-deterministic — human/agent-authored or LLM-translated) and
Stage B (src/noisers/codemix.py, deterministic, no network — see that
module's docstring and the plan for why the split exists).

Merges four sources into data/lexicon/codemix_wordbank.jsonl, in
precedence order (earlier always overwrites later on a sinhala-form
conflict):
  1. The 210 hand-verified entries in data/lexicon/codemix_lexicon.jsonl
     (source: native/loanword, from the original Phase 3 pass)
  2. The reviewed subset of data/lexicon/codemix_candidates_review.csv
     (317 rows as of this writing; source: native/loanword) — nothing in
     the repo previously merged this CSV into any lexicon file at all.
  3. Machine translations from codemix_translation_results.jsonl
     (source: llm), produced by translate_codemix_worklist.py.
  4. data/lexicon/codemix_review_corrections.jsonl — human corrections
     from reviewing data/lexicon/codemix_usage_review.{csv,md} (the
     impact-ordered report of entries that actually fired during
     generation). HIGHEST precedence: overrides sources 1-3 on conflict,
     and can also DELETE an entry outright (action: "remove") regardless
     of which source contributed it. Accumulates across review rounds —
     if the same sinhala form is corrected twice, the LAST line in the
     file wins (plain file-order dict overwrite, same convention as
     load_all_verified() below). Re-running this script after appending
     more corrections is the whole mechanism for a new round; no separate
     "apply corrections" script exists or is needed.

Each row: {sinhala, english, source, codemix_plausible, sold_frequency,
evidence}. Human-verified sources (1, 2, 4) don't carry an LLM plausibility
judgment — they're implicitly plausible (a human already decided they were
worth adding/correcting), so codemix_plausible is always true for them.

Run:  python scripts/build_codemix_wordbank.py
"""

from __future__ import annotations

import hashlib
import json

from _codemix_common import LEXICON_DIR, load_all_verified, log

RESULTS_PATH = LEXICON_DIR / "codemix_translation_results.jsonl"
CORRECTIONS_PATH = LEXICON_DIR / "codemix_review_corrections.jsonl"
WORDBANK_PATH = LEXICON_DIR / "codemix_wordbank.jsonl"
WORDBANK_HASH_PATH = LEXICON_DIR / ".codemix_wordbank.sha256"


def _load_llm_results() -> list[dict]:
    if not RESULTS_PATH.exists():
        return []
    with RESULTS_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_corrections() -> list[dict]:
    if not CORRECTIONS_PATH.exists():
        return []
    with CORRECTIONS_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def main() -> None:
    merged: dict[str, dict] = {}

    # Precedence: apply lowest-precedence source first, then overwrite with
    # higher-precedence sources, so the LAST write for a given sinhala form
    # wins and that's always the most-verified one.
    llm_results = _load_llm_results()
    n_llm = 0
    for row in llm_results:
        merged[row["sinhala"]] = {
            "sinhala": row["sinhala"],
            "english": row["english"],
            "source": "llm",
            "codemix_plausible": row["codemix_plausible"],
            "sold_frequency": row.get("sold_frequency", 0),
            "evidence": row.get("evidence", ""),
        }
        n_llm += 1

    verified = load_all_verified()  # curated lexicon (210) + reviewed CSV (317), curated wins internally
    n_verified = 0
    for sinhala, entry in verified.items():
        merged[sinhala] = {
            "sinhala": sinhala,
            "english": entry["english"],
            "source": entry.get("source", "native"),
            "codemix_plausible": True,  # a human already judged it worth adding
            "sold_frequency": entry.get("sold_frequency", 0),
            "evidence": entry.get("evidence", ""),
        }
        n_verified += 1

    n_before_corrections = len(merged)

    corrections = _load_corrections()
    n_corrected = n_removed = 0
    for row in corrections:
        sinhala = row["sinhala"]
        if row["action"] == "remove":
            if merged.pop(sinhala, None) is not None:
                n_removed += 1
            continue
        if row["action"] == "correct":
            prior = merged.get(sinhala, {})
            merged[sinhala] = {
                "sinhala": sinhala,
                "english": row["english"],
                "source": "human_corrected",
                "codemix_plausible": True,  # a human explicitly approved this exact phrasing
                "sold_frequency": prior.get("sold_frequency", 0),
                "evidence": row.get("note", ""),
            }
            n_corrected += 1
            continue
        raise ValueError(f"unknown correction action {row['action']!r} for {sinhala!r}")

    rows = sorted(merged.values(), key=lambda r: (-r["sold_frequency"], r["sinhala"]))

    log("build_wordbank", f"{n_llm} llm-translated + {n_verified} human-verified "
        f"-> {n_before_corrections} unique entries before corrections "
        f"({n_llm + n_verified - n_before_corrections} overlap, human-verified won)")
    if corrections:
        log("build_wordbank", f"applied {len(corrections)} review corrections: "
            f"{n_corrected} corrected, {n_removed} removed")
    log("build_wordbank", f"-> {len(rows)} unique entries in the final word bank")

    with WORDBANK_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    digest = hashlib.sha256(WORDBANK_PATH.read_bytes()).hexdigest()
    WORDBANK_HASH_PATH.write_text(digest, encoding="utf-8")
    log("build_wordbank", f"wrote {len(rows)} rows -> {WORDBANK_PATH}")
    log("build_wordbank", f"sha256={digest} (first 8: {digest[:8]}) -> {WORDBANK_HASH_PATH}")

    n_plausible = sum(1 for r in rows if r["codemix_plausible"])
    log("build_wordbank", f"{n_plausible}/{len(rows)} entries marked codemix_plausible=true")


if __name__ == "__main__":
    main()
