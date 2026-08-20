"""
Codemix round 5, Stage 1 — mine PHRASE (2-3 word contiguous span) candidates
for code-mix substitution, the mechanism that lets a single switch cover
more CMI than one word can (see the plan: translating more single words
plateaus around mean CMI ~15 regardless of budget, because most of a
post's tokens are closed-class and can never be switched; a span raises
CMI per switch instead of requiring more switches).

--- The candidate filter, and why it isn't "every recurring pair" ---
Mining every adjacent Sinhala pair (the way scripts/build_abbreviate_
initialisms.py mines its bigrams) was tried first and rejected: SOLD's
raw adjacency includes huge numbers of purely closed-class combinations
(the equivalent of "of the") that nobody code-mixes as a unit, and
requiring BOTH words to individually pass round 4's content-word filter
(is_candidate_word) over-corrects the other way -- it excludes exactly
the pattern with the strongest natural evidence in this whole repo: an
English stem attached to the Sinhala light-noun/case-particle "එක"
(scripts/measure_codemix_rate.py's eka_construction_vocabulary, 555 real
SOLD instances). That pattern is content-word + closed-class particle,
not content + content.

The filter here matches that shape: a phrase is a candidate if AT LEAST
ONE word is a genuine content word (is_candidate_word) and NEITHER word is
a slur substring (looks_like_slur checked independently on every word,
never relying on is_candidate_word's slur exclusion alone, since that
function only rejects when the FULL word matches -- belt and suspenders
for a category round 4 treats as a hard, non-negotiable exclusion).

--- What this does NOT do ---
No translation happens here and no API is called (golden rule 5). No
review corrections are read or merged (unlike codemix's word-level
lexicon, there is no pre-existing curated phrase source, so
`already_verified` is always false at this stage -- included in the
schema now so scripts/translate_codemix_worklist.py's existing
already_verified-skip logic extends to phrases without a schema change
later). Nothing here writes to the frozen phrase bank.

Writes data/lexicon/codemix_phrase_worklist.jsonl, one row per unique
(bigram|trigram) candidate type:
  {sinhala, words, n_words, sold_frequency, n_content_words, verb_suspect,
   already_covered_unigram, already_verified, examples}
`already_covered_unigram` flags phrases where every word is ALREADY
individually plausible in the unigram wordbank -- informational only (a
covered phrase still earns the contiguous-span SPF benefit a scattered
pair of single substitutions doesn't), never a filter.

Run:  python scripts/mine_codemix_phrases.py
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _codemix_common import (  # noqa: E402
    LEXICON_DIR, is_candidate_word, log, looks_like_slur, looks_like_verb, sold_posts, text_runs,
)
from src.noisers.codemix import _load_wordbank  # noqa: E402

OUTPUT_PATH = LEXICON_DIR / "codemix_phrase_worklist.jsonl"
OUTPUT_MD_PATH = LEXICON_DIR / "codemix_phrase_worklist.md"

FREQ_FLOOR = 2
MAX_EXAMPLES = 3


def _is_candidate_phrase(words: tuple[str, ...]) -> bool:
    if any(looks_like_slur(w) for w in words):
        return False
    return any(is_candidate_word(w) for w in words)


def mine_phrases() -> tuple[dict, dict]:
    """(ngrams, examples) where ngrams maps a tuple-of-words -> frequency,
    for every back-to-back (whitespace-only between words, matching exactly
    how eligible OCCURRENCES will later be matched at generation time --
    see src/noisers/abbreviate.py's _find_occurrences, the pattern this
    mirrors) Sinhala bigram AND trigram passing _is_candidate_phrase."""
    freq: dict[tuple[str, ...], int] = defaultdict(int)
    examples: dict[tuple[str, ...], list[str]] = defaultdict(list)

    for post in sold_posts():
        text = post["text"]
        runs = text_runs(text)
        seen_this_post: set[tuple[str, ...]] = set()

        # bigrams: S connector(whitespace-only) S
        for i in range(len(runs) - 2):
            is_sin_a, a = runs[i]
            is_conn, connector = runs[i + 1]
            is_sin_b, b = runs[i + 2]
            if not (is_sin_a and is_sin_b) or is_conn or connector.strip() != "":
                continue
            words = (a, b)
            if not _is_candidate_phrase(words):
                continue
            freq[words] += 1
            if words not in seen_this_post:
                seen_this_post.add(words)
                if len(examples[words]) < MAX_EXAMPLES:
                    examples[words].append(text)

        # trigrams: S ws S ws S
        for i in range(len(runs) - 4):
            is_sin_a, a = runs[i]
            is_conn1, conn1 = runs[i + 1]
            is_sin_b, b = runs[i + 2]
            is_conn2, conn2 = runs[i + 3]
            is_sin_c, c = runs[i + 4]
            if not (is_sin_a and is_sin_b and is_sin_c):
                continue
            if is_conn1 or conn1.strip() != "" or is_conn2 or conn2.strip() != "":
                continue
            words = (a, b, c)
            if not _is_candidate_phrase(words):
                continue
            freq[words] += 1
            if words not in seen_this_post:
                seen_this_post.add(words)
                if len(examples[words]) < MAX_EXAMPLES:
                    examples[words].append(text)

    return dict(freq), dict(examples)


def main() -> None:
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)
    wordbank = _load_wordbank()

    freq, examples = mine_phrases()
    n_bigrams_mined = sum(1 for k in freq if len(k) == 2)
    n_trigrams_mined = sum(1 for k in freq if len(k) == 3)
    log("mine_codemix_phrases", f"mined {n_bigrams_mined} distinct bigrams, "
        f"{n_trigrams_mined} distinct trigrams passing the content-word filter")

    candidates = {words: f for words, f in freq.items() if f >= FREQ_FLOOR}
    n_bg_c = sum(1 for k in candidates if len(k) == 2)
    n_tg_c = sum(1 for k in candidates if len(k) == 3)
    log("mine_codemix_phrases", f"{len(candidates)} clear freq>={FREQ_FLOOR} "
        f"({n_bg_c} bigrams, {n_tg_c} trigrams)")

    rows = []
    for words, f in sorted(candidates.items(), key=lambda kv: -kv[1]):
        n_content = sum(1 for w in words if is_candidate_word(w))
        already_covered = all(w in wordbank and wordbank[w]["codemix_plausible"] for w in words)
        rows.append({
            "sinhala": " ".join(words),
            "words": list(words),
            "n_words": len(words),
            "sold_frequency": f,
            "n_content_words": n_content,
            "verb_suspect": any(looks_like_verb(w) for w in words),
            "already_covered_unigram": already_covered,
            "already_verified": False,
            "examples": examples.get(words, []),
        })

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    log("mine_codemix_phrases", f"wrote {len(rows)} candidates -> {OUTPUT_PATH}")

    lines = [
        "# Codemix round 5 — phrase (bigram/trigram) mining worklist",
        "",
        f"{len(rows)} candidates ({n_bg_c} bigrams, {n_tg_c} trigrams), "
        f"freq>={FREQ_FLOOR}, at least 1 content word + no slur substring in "
        "either word. Ranked by SOLD frequency, descending. Nothing here is "
        "translated or approved yet -- see scripts/translate_codemix_worklist.py "
        "(Stage 2/3) and the plan.",
        "",
    ]
    n_already_covered = sum(1 for r in rows if r["already_covered_unigram"])
    lines.append(f"`already_covered_unigram=true` for {n_already_covered}/{len(rows)} "
                 "rows (every word already individually plausible in the unigram "
                 "wordbank) -- informational only, not excluded: a contiguous span "
                 "still earns an SPF benefit scattered singles don't.")
    lines.append("")
    for i, row in enumerate(rows, 1):
        lines.append(f"### {i}. `{row['sinhala']}` (freq={row['sold_frequency']}, "
                      f"n_words={row['n_words']}, content_words={row['n_content_words']}"
                      f"{', VERB-SUSPECT' if row['verb_suspect'] else ''}"
                      f"{', already-covered' if row['already_covered_unigram'] else ''})")
        for ex in row["examples"]:
            lines.append(f"- {ex}")
        lines.append("")
    OUTPUT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    log("mine_codemix_phrases", f"wrote readable version -> {OUTPUT_MD_PATH}")


if __name__ == "__main__":
    main()
