"""
Abbreviation noise vector: collapse an approved two-word Sinhala phrase to
its initials, e.g. a common phrase's first grapheme cluster of each word
joined as "X. Y." -- the way real casual Sinhala texting abbreviates a
fixed phrase, most notably (and most relevantly for a hate-speech
benchmark) offensive multi-word phrases used to soften or evade them.

--- History: this started as a two-channel design, one channel got dropped ---
The original plan also had a Channel A (single-word clipping, e.g. a long
word losing a trailing syllable). Mining it turned out noisy -- see
scripts/build_abbreviate_clippings.py's git history and LOG.md's Phase 4b
Stage 1/2 entries -- and the user's review verdict was blunt: "total
garbage... i dont think that would be a good pathway to abbreviate."
Channel A was removed entirely (code, lexicon, review artifacts), not kept
around unused. This module is therefore single-mechanism: PHRASE
initialism only, what the plan called Channel B.

--- The mechanism ---
A bigram (word1, word2) is eligible only if it's in the frozen, human-
approved data/lexicon/abbreviate_initialisms.jsonl -- 378 bigrams, reviewed
across three passes (single-Sinhala-character-word pairs dropped,
same-word-repeated pairs dropped, different-word-but-same-first-cluster
pairs dropped, see LOG.md). Approval was deliberately OPT-IN: nothing in
this lexicon exists unless a human explicitly approved that exact pair --
see the mining script's docstring for why, given this mechanism's
highest-value use case is modeling evasive obscenity.

A bigram OCCURRENCE is only eligible for substitution when word1 and word2
sit back-to-back in the text with nothing but whitespace between them
(matching exactly how the lexicon was mined -- see `_find_occurrences`).
The abbreviated form is a fixed mechanical rule, `initials()`, shared with
the mining script (which imports it from here) so there is exactly one
definition, never two that could drift apart.

--- Severity: forced-per-post, codemix-shaped ---
Coverage is inherently sparse and post-dependent -- a post either contains
an approved, back-to-back bigram or it doesn't -- so this uses codemix's
forced-selection model rather than misspell/transliteration's probabilistic
one: light abbreviates 1 occurrence if present, heavy abbreviates up to 2,
both capped at however many NON-OVERLAPPING eligible occurrences actually
exist in that post (never an error to have fewer available). Overlap
resolution is greedy left-to-right over the text (a word already consumed
by one occurrence can't also start or end a second one in the same pass) --
deterministic by construction, no rng involved in which occurrences are
even eligible, only in which of the eligible ones get chosen.

TARGET_NOISE_RATE below is measured once from a completed generation run,
same as codemix's -- a drift TRIPWIRE for eval/harness.py's
noise_rate_error, not a rate this module tunes toward. `n_substitutions`
is populated (bigram occurrences actually abbreviated), the second noiser
after codemix to use that schema field for real.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import clusters, text_runs  # noqa: E402

LEXICON_PATH = REPO_ROOT / "data" / "lexicon" / "abbreviate_initialisms.jsonl"
LEXICON_HASH_PATH = REPO_ROOT / "data" / "lexicon" / ".abbreviate_initialisms.sha256"

# How many DISTINCT bigram OCCURRENCES are force-substituted per post, at
# each severity -- capped at however many non-overlapping eligible
# occurrences are actually present (see check_abbreviate_substitution_spec
# in eval/invariants.py for the exact contract).
_BIGRAMS_PER_POST = {"light": 1, "heavy": 2}

# Measured once from a completed generation run (see LOG.md's Phase 4b
# Stage 5 entry) -- a drift tripwire, not a natural-rate claim. See the
# module docstring's "Severity" section and src/noisers/codemix.py's
# TARGET_NOISE_RATE docstring for why forced-per-post selection makes this
# a consequence of post length and lexicon coverage, not something tuned.
TARGET_NOISE_RATE = {"light": 0.0, "heavy": 0.0}


def initials(word1: str, word2: str) -> str:
    """The mechanical abbreviation rule: first grapheme cluster of each
    word, joined as "X. Y." -- the ONLY place this rule is defined;
    scripts/build_abbreviate_initialisms.py imports this rather than
    keeping its own copy, so mining, review display, and generation can
    never disagree about what an approved bigram actually produces."""
    return f"{clusters(word1)[0]}. {clusters(word2)[0]}."


def _lexicon_version_suffix() -> str:
    if LEXICON_HASH_PATH.exists():
        digest = LEXICON_HASH_PATH.read_text(encoding="utf-8").strip()
        return digest[:8] if digest else "unbuilt"
    return "unbuilt"


GENERATOR_VERSION = f"abbreviate-v1+{_lexicon_version_suffix()}"

_lexicon_cache: set[tuple[str, str]] | None = None


def _load_lexicon() -> set[tuple[str, str]]:
    global _lexicon_cache
    if _lexicon_cache is None:
        pairs: set[tuple[str, str]] = set()
        if LEXICON_PATH.exists():
            with LEXICON_PATH.open(encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        row = json.loads(line)
                        pairs.add((row["word1"], row["word2"]))
        _lexicon_cache = pairs
    return _lexicon_cache


def _find_occurrences(runs: list[tuple[bool, str]], lexicon: set[tuple[str, str]]) -> list[tuple[int, str, str]]:
    """[(run_index_of_word1, word1, word2), ...] for every back-to-back
    (whitespace-only between them, matching exactly how the lexicon was
    mined) Sinhala word pair in `runs` that's in the approved lexicon, in
    left-to-right text order."""
    occurrences = []
    for i in range(len(runs) - 2):
        is_sin_a, a = runs[i]
        is_conn, connector = runs[i + 1]
        is_sin_b, b = runs[i + 2]
        if not (is_sin_a and is_sin_b):
            continue
        if is_conn or connector.strip() != "":
            continue
        if (a, b) in lexicon:
            occurrences.append((i, a, b))
    return occurrences


def _non_overlapping(occurrences: list[tuple[int, str, str]]) -> list[tuple[int, str, str]]:
    """Greedy left-to-right selection so no two eligible occurrences share a
    word run -- e.g. in "A B C" where both (A,B) and (B,C) are approved
    bigrams, only the first (leftmost) is kept, since B can't be consumed by
    two substitutions in one pass. Deterministic by construction (text
    order, not rng)."""
    kept = []
    next_free_index = -1
    for run_index, w1, w2 in occurrences:
        if run_index <= next_free_index:
            continue
        kept.append((run_index, w1, w2))
        next_free_index = run_index + 2  # word2's run index
    return kept


def _apply(text: str, severity: str, seed: int) -> tuple[str, float, int]:
    """Core implementation, shared by apply() (2-tuple, used by the harness's
    generic noiser-case runner and check_determinism, which both unpack
    exactly 2 values -- see eval/harness.py) and by anything that also needs
    n_substitutions (generate_abbreviate.py's row-writing loop). One
    implementation only, so the two callers can never drift apart --
    mirrors src/noisers/codemix.py's _apply()/apply() split.

    Returns (noisy_text, realised_noise_rate, n_substitutions).
    """
    if severity not in _BIGRAMS_PER_POST:
        raise ValueError(f"unknown severity {severity!r}, expected one of {list(_BIGRAMS_PER_POST)}")

    k = _BIGRAMS_PER_POST[severity]
    lexicon = _load_lexicon()
    runs = text_runs(text)
    n_words = sum(1 for is_sinhala, _run in runs if is_sinhala)

    occurrences = _non_overlapping(_find_occurrences(runs, lexicon))

    rng = random.Random(seed)
    # occurrences is already in deterministic left-to-right text order (not
    # derived from set/dict iteration), so sampling directly from it carries
    # no PYTHONHASHSEED risk -- see codemix.py's docstring for the bug this
    # guards against.
    chosen_indices = set(rng.sample(range(len(occurrences)), min(k, len(occurrences))))
    chosen_by_run_index = {occ[0]: occ for j, occ in enumerate(occurrences) if j in chosen_indices}

    out_parts: list[str] = []
    skip_until = -1
    n_altered_words = 0
    for i, (is_sinhala, run) in enumerate(runs):
        if i <= skip_until:
            continue
        match = chosen_by_run_index.get(i)
        if match is not None:
            _run_index, w1, w2 = match
            out_parts.append(initials(w1, w2))
            n_altered_words += 2
            skip_until = i + 2
            continue
        out_parts.append(run)

    n_substitutions = len(chosen_indices)
    realised_noise_rate = (n_altered_words / n_words) if n_words else 0.0
    return "".join(out_parts), realised_noise_rate, n_substitutions


def apply(text: str, severity: str, seed: int) -> tuple[str, float]:
    """Sinhala -> abbreviated text at the given severity ("light" | "heavy").

    Returns (noisy_text, realised_noise_rate). Deterministic: the same
    (text, severity, seed, frozen lexicon file) always produces the same
    output. Thin 2-tuple wrapper around _apply() -- see its docstring.
    """
    noisy_text, realised_noise_rate, _n_substitutions = _apply(text, severity, seed)
    return noisy_text, realised_noise_rate
