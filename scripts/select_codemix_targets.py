"""
Phase 3 redesign, Stage A step 1 — select the code-mix TARGET vocabulary:
for every SOLD post, the top-4 candidate Sinhala content words by corpus
frequency (after the closed-class stoplist), unioned across all 10,000
posts. See LOG.md / the plan for why per-post ranking (not a corpus-wide
frequency cutoff) is the right unit: it bounds the translation job to what
posts actually need while still reaching effectively every post.

N=4 leaves two fallback candidates per severity slot (heavy substitutes 2)
for words later judged implausible or untranslatable. Measured on this
corpus: N=4 -> 5,933 unique word types, covering 9,995/10,000 posts with
>=1 candidate.

This script makes NO translation decisions and calls no API. It writes:
  data/lexicon/codemix_translation_worklist.jsonl
    one row per unique candidate word type:
    {sinhala, sold_frequency, n_posts_top4, verb_suspect, slur_flag,
     already_verified, examples: [<=3 real SOLD sentences containing it]}

`already_verified` rows (already translated in the 210-entry curated
lexicon or the 317 reviewed rows of codemix_candidates_review.csv) are
included for completeness/inspection but Step 2 (translate_codemix_worklist.py)
skips them — no need to spend API budget re-translating a word a human
already verified.

Run:  python scripts/select_codemix_targets.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict

from _codemix_common import (
    LEXICON_DIR,
    is_candidate_word,
    load_all_verified,
    log,
    looks_like_slur,
    looks_like_verb,
    sold_posts,
    text_runs,
)

TOP_N_PER_POST = 4
MAX_EXAMPLES = 3
OUTPUT_PATH = LEXICON_DIR / "codemix_translation_worklist.jsonl"


def main() -> None:
    posts = sold_posts()
    log("select_codemix_targets", f"loaded {len(posts)} SOLD posts (train+test)")

    # Pass 1: corpus-wide frequency of every candidate word, and each post's
    # distinct candidate word set (needed twice: once to rank, once to
    # collect examples in pass 2).
    freq: Counter[str] = Counter()
    post_candidates: list[tuple[dict, list[str]]] = []
    for post in posts:
        words = {run for is_sinhala, run in text_runs(post["text"]) if is_sinhala}
        candidates = [w for w in words if is_candidate_word(w)]
        post_candidates.append((post, candidates))
        freq.update(candidates)

    # Pass 2: per post, rank its candidates by (-corpus_freq, word) — the
    # `word` tiebreak makes this a pure function of the frequency table,
    # independent of dict/set iteration order. Take top TOP_N_PER_POST.
    # Union across posts = the eligibility set. Track how many posts each
    # word appears in a top-4 slot for (impact signal, not just raw freq).
    n_posts_top4: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    posts_with_candidate = 0
    for post, candidates in post_candidates:
        if not candidates:
            continue
        posts_with_candidate += 1
        ranked = sorted(candidates, key=lambda w: (-freq[w], w))[:TOP_N_PER_POST]
        for w in ranked:
            n_posts_top4[w] += 1
            if len(examples[w]) < MAX_EXAMPLES:
                examples[w].append(post["text"])

    eligibility_set = sorted(n_posts_top4)
    log("select_codemix_targets",
        f"posts with >=1 candidate word: {posts_with_candidate}/{len(posts)}")
    log("select_codemix_targets",
        f"eligibility set (union of top-{TOP_N_PER_POST}-per-post): {len(eligibility_set)} unique word types")

    verified = load_all_verified()
    log("select_codemix_targets",
        f"{len(verified)} words already have a human-verified translation")

    rows = []
    n_already = 0
    for w in eligibility_set:
        already = w in verified
        n_already += already
        rows.append({
            "sinhala": w,
            "sold_frequency": freq[w],
            "n_posts_top4": n_posts_top4[w],
            "verb_suspect": looks_like_verb(w),
            "slur_flag": looks_like_slur(w),
            "already_verified": already,
            "examples": examples[w],
        })
    rows.sort(key=lambda r: (-r["n_posts_top4"], -r["sold_frequency"], r["sinhala"]))

    log("select_codemix_targets",
        f"{n_already} already verified (skip translation); "
        f"{len(rows) - n_already} need translation in Step 2")

    LEXICON_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    log("select_codemix_targets", f"wrote {len(rows)} rows -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
