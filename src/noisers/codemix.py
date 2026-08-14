"""
Code-mixing noise vector: substitute a real, attested English word for a
Sinhala word, leaving the rest of the Sinhala matrix intact — e.g.
"ආණ්ඩුව අසාධාරණයි" -> "government එක අසාධාරණයි". This is a WORD-CHOICE
operation (which language a word is written in), deliberately orthogonal
to transliteration's SCRIPT/SPELLING operation — see src/pipeline.py for
why codemix therefore runs BEFORE transliteration in the compound order.

--- v2: forced per-post selection, on-demand-translated word bank ---
v1 (see LOG.md "Phase 3 density expansion") ran an independent Bernoulli
trial per eligible word against a 210-entry hand-curated lexicon. Nothing
was sentence-aware, so 85.8%/79.7% of light/heavy output rows came out
byte-identical to their source, and only 21.8% of posts even contained a
matchable word — a coverage ceiling from the lexicon size, not a
severity-tuning problem.

v2 fixes both causes. Selection is now FORCED and per-post: light
substitutes exactly 1 word type, heavy exactly 2 (capped at however many
eligible types are actually present in that post — never an error, just a
cap). The word bank (data/lexicon/codemix_wordbank.jsonl) was built by
translating the top-4-by-corpus-frequency candidate words of every SOLD
post — 7,969 unique word types, reaching 9,934/10,000 posts — via a
one-time offline batch (see scripts/select_codemix_targets.py,
scripts/translate_codemix_worklist.py, scripts/build_codemix_wordbank.py).
That batch mixed human-verified entries (the original 210-entry lexicon,
plus 317 previously-unmerged reviewed rows) with LLM-translated ones, each
carrying a `codemix_plausible` flag — would a bilingual Sri Lankan speaker
actually say this English word inside a Sinhala sentence? Selection prefers
plausible words and falls back to implausible ones only when a post has no
plausible candidate at all, trading some naturalness for coverage rather
than leaving the post untouched (see the plan's "honest tradeoff" section
and LOG.md: across every mining pass tried, only ~5-7% of candidate words
turned out to be genuinely viable code-mix targets — forcing a
substitution into every post means some substitutions land on words that
aren't natural swap targets, mitigated but not eliminated by the
plausibility gate and the impact-ordered human review in
scripts/build_codemix_usage_report.py).

Word bank keys are EXACT SURFACE FORMS observed in SOLD (Sinhala is
agglutinative; case lives in suffixes, e.g. "ආණ්ඩුවට" (to the government)
is a separate entry from "ආණ්ඩුව", not runtime-inflected) — this noiser
never does morphological analysis, only verified/translated surface
substitution.

--- Why this stays deterministic despite an LLM having translated most of
the word bank ---
Translation happened ONCE, offline, in Stage A (see the three scripts
above) and its output was frozen into codemix_wordbank.jsonl before this
module ever runs. apply() is a pure function of (text, severity, seed, the
frozen wordbank file on disk) — no network call happens here, ever,
satisfying golden rule 5 ("do not call the live endpoint in a loop":
translation isn't a loop, it's a one-time offline build step) and golden
rule 4 (determinism: same input + same seed + same wordbank file -> same
output, always). GENERATOR_VERSION is stamped with the wordbank's own
SHA-256 (first 8 hex chars) specifically so a wordbank rebuild is always
visible in every output row's generator_version, even though the bank
itself isn't part of the (text, severity, seed) function signature.

--- Why TARGET_NOISE_RATE is a tripwire, not a target ---
Under forced selection, realised_noise_rate is a CONSEQUENCE of post length
(more Sinhala words in a post -> smaller fraction altered by the same fixed
substitution count), not something this module tunes toward. The real
design spec — light substitutes 1 type, heavy substitutes 2, capped at
availability — is checked directly by eval/invariants.py's
check_codemix_substitution_spec. TARGET_NOISE_RATE below is measured ONCE
from a completed generation run and hard-coded purely so
eval/harness.py's noise_rate_error can catch unintended drift (a corrupted
wordbank, a corpus change) — it is not a natural-rate claim. The resulting
density is well above the ~1.0-1.8% natural Sinhala-English code-mix rate
measured in data/lexicon/codemix_reference_stats.json; that gap is a
deliberate, documented trade of natural-rate fidelity for benchmark signal
density (LOG.md: "prioritize density over natural-rate realism"), not an
oversight.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402

LEXICON_PATH = REPO_ROOT / "data" / "lexicon" / "codemix_wordbank.jsonl"
WORDBANK_HASH_PATH = REPO_ROOT / "data" / "lexicon" / ".codemix_wordbank.sha256"

# How many DISTINCT word TYPES are force-substituted per post, at each
# severity — capped at the number of eligible types actually present (never
# an error to have fewer than this available; see eval/invariants.py's
# check_codemix_substitution_spec for the exact contract).
_WORDS_PER_POST = {"light": 1, "heavy": 2}

# Measured once from a completed generation run — see the module docstring's
# "Why TARGET_NOISE_RATE is a tripwire, not a target" section. Pooled mean
# realised_noise_rate across train+test (10,000 posts), wordbank sha256
# e3c5381c... (4,118 entries: after all 3 human review rounds — 910
# corrected, 82 removed total from the original 4,200-entry build; see
# data/lexicon/codemix_review_corrections.jsonl and LOG.md — the review is
# COMPLETE as of this build, covering the entire codemix_usage_review.md
# document). 93.2%/93.9% (train/test) of posts had >=1 eligible word and
# were touched.
TARGET_NOISE_RATE = {"light": 0.0884, "heavy": 0.1317}


def _wordbank_version_suffix() -> str:
    if WORDBANK_HASH_PATH.exists():
        digest = WORDBANK_HASH_PATH.read_text(encoding="utf-8").strip()
        return digest[:8] if digest else "unbuilt"
    return "unbuilt"


GENERATOR_VERSION = f"codemix-v2+{_wordbank_version_suffix()}"

_wordbank_cache: dict[str, dict] | None = None


def _load_wordbank() -> dict[str, dict]:
    global _wordbank_cache
    if _wordbank_cache is None:
        if LEXICON_PATH.exists():
            with LEXICON_PATH.open(encoding="utf-8") as f:
                _wordbank_cache = {
                    row["sinhala"]: {"english": row["english"], "codemix_plausible": row["codemix_plausible"]}
                    for row in (json.loads(line) for line in f if line.strip())
                }
        else:
            _wordbank_cache = {}
    return _wordbank_cache


def _apply(text: str, severity: str, seed: int) -> tuple[str, float, list[str]]:
    """Core implementation, shared by apply() (2-tuple, used by the harness
    and generate_codemix.py's row-writing loop) and by anything that also
    needs to know WHICH word types were substituted (generate_codemix.py's
    n_substitutions field, scripts/build_codemix_usage_report.py's impact
    accounting) — one implementation, so the report can never drift from
    what was actually generated.

    Returns (noisy_text, realised_noise_rate, substituted_types).
    substituted_types is sorted for determinism (see the `sorted()` note
    below) — never rely on insertion/set order from this function's internals.
    """
    if severity not in _WORDS_PER_POST:
        raise ValueError(f"unknown severity {severity!r}, expected one of {list(_WORDS_PER_POST)}")

    k = _WORDS_PER_POST[severity]
    wordbank = _load_wordbank()
    runs = list(text_runs(text))
    sinhala_words = [run for is_sinhala, run in runs if is_sinhala]
    n_words = len(sinhala_words)

    # sorted() here is a CORRECTNESS requirement, not style: Python
    # randomises str hashing per process, so sampling from an unsorted set
    # would produce different output across separate runs of the same
    # (text, severity, seed) — a determinism break that eval/invariants.py's
    # check_determinism would NOT catch, since it compares two trials within
    # one process. See the plan / LOG.md for how this was caught.
    eligible = sorted({w for w in sinhala_words if w in wordbank})
    plausible = [w for w in eligible if wordbank[w]["codemix_plausible"]]
    # Prefer natural-sounding substitutions; fall back to the full eligible
    # pool only when NOTHING plausible is available, trading naturalness
    # for coverage rather than leaving the post untouched. See the module
    # docstring's "honest tradeoff" discussion.
    pool = plausible if plausible else eligible

    rng = random.Random(seed)
    chosen = set(rng.sample(pool, min(k, len(pool))))

    out_parts: list[str] = []
    n_altered = 0
    for is_sinhala, run in runs:
        if is_sinhala and run in chosen:
            out_parts.append(wordbank[run]["english"])
            n_altered += 1
        else:
            out_parts.append(run)

    realised_noise_rate = (n_altered / n_words) if n_words else 0.0
    return "".join(out_parts), realised_noise_rate, sorted(chosen)


def apply(text: str, severity: str, seed: int) -> tuple[str, float]:
    """Sinhala -> code-mixed text at the given severity ("light" | "heavy").

    Returns (noisy_text, realised_noise_rate). Deterministic: the same
    (text, severity, seed, wordbank file) always produces the same output.
    Kept as a thin 2-tuple wrapper around _apply() because the harness's
    generic noiser-case runner and check_determinism both unpack exactly 2
    values from every noiser's apply() — see eval/harness.py.
    """
    noisy_text, realised_noise_rate, _substituted = _apply(text, severity, seed)
    return noisy_text, realised_noise_rate
