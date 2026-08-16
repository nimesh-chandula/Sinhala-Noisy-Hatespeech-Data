"""
Transliteration noise vector: render clean Sinhala as romanized Singlish,
via the Phase 1 winner (aksharamukha_colloquial, with the v->w and ත/ට
corrections — see src/romanizers/aksharamukha.py).

Both severities produce FULLY Latin-script output — never leave some words
in native Sinhala script at "light" severity. Doing so would inject Sinhala
Unicode codepoints alongside Latin ones into the same text, diverging from
the (pure-Latin) reference corpus for reasons that reflect a metric-scope
mismatch rather than genuine unrealism, and it conceptually overlaps with
the separate `codemix` vector (Phase 3) anyway.

Instead, severity is SPELLING-VARIANCE INTENSITY: every word is always
transliterated, but "heavy" substitutes a real, attested alternate spelling
for a higher fraction of words than "light" does — mimicking a more casual
or inconsistent typist, the way real people don't spell the same word the
same way every time. Variants come from data/lexicon/word_variants.jsonl
(built by scripts/build_word_variants.py from the same Swa-Bhasha data
data/gold/gold_words.jsonl uses — restricted to SOLD's actual vocabulary,
excluding the 2000 words in data/gold/heldout_words.txt so generation never
leaks the CER gold set's answers into itself).

`realised_noise_rate` = the fraction of words that received a non-canonical
(variant) spelling — this is what `noise_rate_error` checks against
TARGET_NOISE_RATE per severity.

--- coverage calibration ---
Only ~86% of SOLD's Sinhala word tokens have an entry in the variant
lookup (149,437/173,895 measured over the full train+test corpus) — the
rest have no attested alternate spelling to offer. A first attempt used
TARGET_NOISE_RATE directly as the per-word substitution probability, which
silently caps the realised rate at ~86% of the target (measured: light hit
0.096 vs a 0.2 target — 4x outside the 0.05 tolerance). _ATTEMPT_PROBABILITY
corrects for this: probability = target_rate / _COVERAGE, so the REALISED
rate (which is what noise_rate_error actually checks) lands on target.

--- variant-selection and rate tuning (Phase 2 finding — target NOT fully met) ---
Measured against the full corpus: the plain canonical baseline (zero
variance) already scores realism_jsd=0.109 — much better than an early
500-post estimate suggested, and only ~14x the theoretical floor (0.008,
reference vs itself). Uniform-random variant selection at 0.2/0.5 target
rates made this WORSE (light 0.107 ~flat, heavy 0.133 — 22% worse than
baseline), because Swa-Bhasha's attested variants skew toward heavily
truncated/vowel-dropped spellings (e.g. "waladi" -> "wald"), and uniform
sampling over-represents them relative to how often real typists actually
use them. Switching to CLOSEST-variant selection (by CER to canonical, a
proxy for "smallest plausible deviation") helped, and a rate sweep (0, .05,
.1, .15, .2, .3) found a narrow band around 0.10-0.15 giving the best
result — but that best case is only realism_jsd=0.105, a ~4% reduction
against a 30% target. Beyond ~0.15 the benefit reverses (0.30 -> back to
0.109, no better than baseline). This looks like a genuine plateau for this
lever, not a tuning miss: the remaining gap is most likely SOLD-vs-Swa-
Bhasha topic/vocabulary differences (hate-speech-focused posts vs general
social media), which spelling variance can't address. Kept as a modest,
real (if small) improvement rather than reverted, since it doesn't regress
anything — but the 30% target was NOT reached; see LOG.md.
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
from src.romanizers.aksharamukha import romanize_colloquial  # noqa: E402
from eval.gold_cer import cer  # noqa: E402

LEXICON_PATH = REPO_ROOT / "data" / "lexicon" / "word_variants.jsonl"

TARGET_NOISE_RATE = {"light": 0.10, "heavy": 0.20}

# Measured fraction of SOLD Sinhala word tokens with >=1 attested variant
# (see docstring). Used to convert a target REALISED rate into the
# per-word attempt probability that actually produces it.
_COVERAGE = 0.8594
_ATTEMPT_PROBABILITY = {sev: min(1.0, rate / _COVERAGE) for sev, rate in TARGET_NOISE_RATE.items()}

GENERATOR_VERSION = "transliteration-v2"

_variants_cache: dict[str, list[str]] | None = None


def _load_variants() -> dict[str, list[str]]:
    global _variants_cache
    if _variants_cache is None:
        if LEXICON_PATH.exists():
            with LEXICON_PATH.open(encoding="utf-8") as f:
                _variants_cache = {
                    row["sinhala"]: row["romanizations"]
                    for row in (json.loads(line) for line in f if line.strip())
                }
        else:
            _variants_cache = {}
    return _variants_cache


def _is_abbreviation_fragment(runs: list[tuple[bool, str]], i: int) -> bool:
    """True if the Sinhala run at index i in `runs` looks like one half of
    src.noisers.abbreviate's initials() output ("X. Y.") -- a single
    grapheme cluster immediately joined to a literal ". " (as word1) or
    immediately preceded by one (as word2). Structural pattern match, not a
    flag passed in from abbreviate itself, so this module stays decoupled
    from abbreviate.py entirely (see apply()'s `mixed_script_rate` docstring
    for why this needs to be detected at all: leaving one half of an
    abbreviation pair in Sinhala script while romanizing the other would
    read as broken, not as realistic mixing)."""
    is_sinhala, run = runs[i]
    if not is_sinhala or len(clusters(run)) != 1:
        return False
    if i + 1 < len(runs) and runs[i + 1] == (False, ". "):
        return True
    if i - 1 >= 0 and runs[i - 1] == (False, ". "):
        return True
    return False


def apply(text: str, severity: str, seed: int, mixed_script_rate: float = 0.0) -> tuple[str, float]:
    """Sinhala -> Singlish at the given severity ("light" | "heavy").

    Returns (noisy_text, realised_noise_rate). Deterministic: the same
    (text, severity, seed, mixed_script_rate) always produces the same
    output — a single random.Random(seed) is consumed sequentially over
    words in left-to-right order, which is itself a deterministic function
    of the input text.

    `mixed_script_rate` defaults to 0.0, reproducing this module's original
    behavior EXACTLY (every Sinhala word gets romanized, per the module
    docstring's "both severities produce FULLY Latin-script output" design)
    — the standalone `transliteration` condition's generation script never
    passes this argument, so its output is untouched by this parameter's
    existence. It exists only for src/pipeline.py's compound condition,
    where the user asked for a REAL script mixture (some words stay in
    Sinhala, some get romanized) rather than the standalone condition's
    uniform full-Latin output. When > 0.0: `mixed_script_rate` is the
    fraction of Sinhala words that get romanized at all (the rest are left
    byte-identical to the input) -- an ordinary word's fate is an
    independent coin flip, EXCEPT a word produced by abbreviate's
    initials() (detected structurally, see _is_abbreviation_fragment) is
    ALWAYS romanized, never subject to the flip, so an abbreviation pair
    can't end up half-Sinhala/half-Latin. In this mode realised_noise_rate
    is redefined to mean "fraction of Sinhala words that got romanized at
    all" (the mixing outcome itself), not the standalone mode's "fraction
    with a non-canonical spelling" -- a different, more relevant notion of
    alteration for what this mode is measuring.
    """
    if severity not in TARGET_NOISE_RATE:
        raise ValueError(f"unknown severity {severity!r}, expected one of {list(TARGET_NOISE_RATE)}")

    attempt_probability = _ATTEMPT_PROBABILITY[severity]
    variants = _load_variants()
    rng = random.Random(seed)

    if mixed_script_rate <= 0.0:
        out_parts: list[str] = []
        n_words = 0
        n_altered = 0
        for is_sinhala, run in text_runs(text):
            if not is_sinhala:
                out_parts.append(run)
                continue
            n_words += 1
            canonical = romanize_colloquial(run)
            word_variants = variants.get(run)
            chosen = canonical
            if word_variants and rng.random() < attempt_probability:
                # Closest variant to canonical (by CER), not uniform random —
                # see module docstring: uniform selection over-represents rare,
                # heavily-truncated attested spellings and hurt realism_jsd.
                chosen = min(word_variants, key=lambda v: cer(v, canonical))
            if chosen != canonical:
                n_altered += 1
            out_parts.append(chosen)

        realised_noise_rate = (n_altered / n_words) if n_words else 0.0
        return "".join(out_parts), realised_noise_rate

    # --- mixed-script mode (compound pipeline only) ---
    runs = text_runs(text)
    out_parts = []
    n_words = 0
    n_romanized = 0
    for i, (is_sinhala, run) in enumerate(runs):
        if not is_sinhala:
            out_parts.append(run)
            continue
        n_words += 1
        force_romanize = _is_abbreviation_fragment(runs, i)
        if not force_romanize and rng.random() >= mixed_script_rate:
            out_parts.append(run)  # stays in Sinhala script, byte-identical
            continue
        n_romanized += 1
        canonical = romanize_colloquial(run)
        word_variants = variants.get(run)
        chosen = canonical
        if word_variants and rng.random() < attempt_probability:
            chosen = min(word_variants, key=lambda v: cer(v, canonical))
        out_parts.append(chosen)

    realised_noise_rate = (n_romanized / n_words) if n_words else 0.0
    return "".join(out_parts), realised_noise_rate
