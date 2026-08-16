"""
Shared helpers for the Phase 3 code-mix redesign scripts
(select_codemix_targets.py, translate_codemix_worklist.py,
build_codemix_wordbank.py, build_codemix_usage_report.py). Not a noiser
module itself — src/noisers/codemix.py never imports this; it only reads
the frozen data/lexicon/codemix_wordbank.jsonl these scripts produce.

Centralizes the two things every one of those scripts needs and that must
stay IDENTICAL across all of them: how a Sinhala word is tokenized/counted
(must match src.graphemes.text_runs, the same tokenizer the noiser uses) and
how the two pre-existing "already verified" sources are read (the 210-entry
hand-curated data/lexicon/codemix_lexicon.jsonl, and the 317 rows with a
filled proposed_english in data/lexicon/codemix_candidates_review.csv that
nothing in the repo has merged anywhere yet).
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402

# scripts/ is on sys.path[0] when any script here is run directly, so this
# import works without extra path manipulation.
import mine_codemix_candidates as _miner  # noqa: E402
import classify_codemix_candidates as _classifier  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
SOLD_DIR = DATA_DIR / "sold"
LEXICON_DIR = DATA_DIR / "lexicon"
CURATED_LEXICON_PATH = LEXICON_DIR / "codemix_lexicon.jsonl"
CANDIDATES_CSV_PATH = LEXICON_DIR / "codemix_candidates_review.csv"

# Re-exported so every script filters candidates identically. STOPLIST and
# VERB_SUFFIXES live in mine_codemix_candidates.py; SLUR_SUBSTRINGS (plus the
# adjective/family/idiomatic-abstract/low-plausibility category sets) lives in
# classify_codemix_candidates.py — two different scripts, easy to conflate.
STOPLIST = _miner._STOPLIST
VERB_SUFFIXES = _miner._VERB_SUFFIXES
SLUR_SUBSTRINGS = _classifier._SLUR_SUBSTRINGS
ADJECTIVE_INTENSIFIER = _classifier._ADJECTIVE_INTENSIFIER
FAMILY_TERMS = _classifier._FAMILY_TERMS
IDIOMATIC_ABSTRACT = _classifier._IDIOMATIC_ABSTRACT
LOW_PLAUSIBILITY_CONCRETE = _classifier._LOW_PLAUSIBILITY_CONCRETE
EXTRA_FUNC = _classifier._EXTRA_FUNC
EXTRA_PRONOUNS = _classifier._EXTRA_PRONOUNS
VERB_FORMS = _classifier._VERB_FORMS

# Words found by directly eyeballing the top-30 highest-impact rows of the
# first worklist run (the checkpoint the plan calls for, before spending API
# budget) that none of the imported category sets caught:
#   අර    "that (yonder)" — demonstrative, same closed class as මේ/ඒ in
#         STOPLIST, just missing from it.
#   ගෙවල් / රට / රටේ-family etc. are legitimate content words (kept); the
#   ones excluded below are specifically closed-class/discourse items.
_ADDITIONAL_STOPWORDS = {"අර", "අරක", "අරවා", "අරයා", "අරාවට"}

# All non-content categories combined into one filter set, applied on top of
# the base STOPLIST. Everything here was already being auto-tagged as
# non-viable by classify_codemix_candidates.py under the old pipeline
# ("func", "adjective/intensifier", "family/kinship", "verb form",
# "idiomatic/abstract", "low real-world code-mix plausibility") — folding
# it into candidate SELECTION here means the LLM translation budget in Step 2
# is never spent on words a deterministic rule would reject anyway.
NON_CONTENT_WORDS = (
    EXTRA_FUNC | EXTRA_PRONOUNS | ADJECTIVE_INTENSIFIER | FAMILY_TERMS
    | IDIOMATIC_ABSTRACT | LOW_PLAUSIBILITY_CONCRETE | VERB_FORMS
    | _ADDITIONAL_STOPWORDS
)
MIN_WORD_GRAPHEMES = 2  # drop single-grapheme "words" (stray punctuation runs)


def log(prefix: str, msg: str) -> None:
    print(f"[{prefix}] {msg}")


def sold_posts() -> list[dict]:
    """All SOLD posts, train+test, each {"post_id", "text", "label", "split"}."""
    posts = []
    for split in ("train", "test"):
        with (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    row = json.loads(line)
                    row["split"] = split
                    posts.append(row)
    return posts


def is_candidate_word(word: str) -> bool:
    """Closed-class / non-content / slur filter, applied BEFORE anything is
    ranked, translated, or shown to an LLM.

    NON_CONTENT_WORDS (func words, pronouns, adjectives/intensifiers, family
    terms, idiomatic-abstract, low-plausibility-concrete, literal verb forms)
    is a hard exclusion, not just an annotation: every one of these
    categories was already being auto-tagged as non-viable by
    classify_codemix_candidates.py under the old pipeline, so this is
    established project judgment, not a new call.

    Slurs (SLUR_SUBSTRINGS) are ALSO a hard exclusion here, even though the
    plan text considered making them annotation-only like the verb-suffix
    heuristic. Upgraded after the Step-1 checkpoint spot-check surfaced
    ගොන්/පුක/සක්කිලි among the top-30 highest-impact candidates in this
    hate-speech-labeled corpus — a slur should never enter the translation
    worklist or the wordbank at all, not be merely down-weighted by a
    plausibility flag that a coverage fallback could still override.

    The suffix-based verb heuristic (looks_like_verb) is deliberately NOT a
    filter here, per its own docstring in mine_codemix_candidates.py: it is
    imprecise by design and used only to annotate.
    """
    if word in STOPLIST:
        return False
    if word in NON_CONTENT_WORDS:
        return False
    if looks_like_slur(word):
        return False
    if len(word) < MIN_WORD_GRAPHEMES:
        return False
    return True


def looks_like_verb(word: str) -> bool:
    return any(word.endswith(suf) for suf in VERB_SUFFIXES)


def looks_like_slur(word: str) -> bool:
    return any(root in word for root in SLUR_SUBSTRINGS)


def load_curated_lexicon() -> list[dict]:
    """The 210 hand-verified entries: {sinhala, english, source, sold_frequency, evidence}."""
    if not CURATED_LEXICON_PATH.exists():
        return []
    with CURATED_LEXICON_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_reviewed_candidates() -> list[dict]:
    """The subset of the 12,000-row candidate CSV that already carries a
    reviewed English translation (317 rows as of this writing): final_english
    if set, else proposed_english where confidence_note starts "reviewed (".
    The CSV is BOM-encoded (utf-8-sig) — every script reading it must say so
    explicitly or the first column name silently gains a BOM prefix.
    """
    if not CANDIDATES_CSV_PATH.exists():
        return []
    out = []
    with CANDIDATES_CSV_PATH.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            final = (row.get("final_english") or "").strip()
            proposed = (row.get("proposed_english") or "").strip()
            note = row.get("confidence_note") or ""
            english = final or (proposed if note.startswith("reviewed (") else "")
            if not english:
                continue
            source = "loanword" if note.startswith("reviewed (loanword") else "native"
            out.append({
                "sinhala": row["sinhala"],
                "english": english,
                "source": source,
                "sold_frequency": int(row["sold_frequency"]) if row.get("sold_frequency") else 0,
                "evidence": note,
            })
    return out


def load_all_verified() -> dict[str, dict]:
    """Merge the two verified sources into one {sinhala: entry} map. The
    curated lexicon (already hand-verified, source native/loanword) wins on
    conflict — there should be none in practice since the CSV mining script
    excludes words already in the curated lexicon, but precedence is
    explicit rather than accidental.
    """
    merged: dict[str, dict] = {}
    for entry in load_reviewed_candidates():
        merged[entry["sinhala"]] = entry
    for entry in load_curated_lexicon():
        merged[entry["sinhala"]] = entry
    return merged
