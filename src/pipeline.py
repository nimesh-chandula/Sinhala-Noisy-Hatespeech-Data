"""
Compound noising pipeline: applies noise vectors in a fixed order to produce
the "compound" condition (Phase 5).

Fixed order (do not reorder between runs — determinism depends on it):
    codemix -> abbreviate -> transliteration -> misspell

--- Why codemix and abbreviate both run before transliteration ---
Codemix and abbreviate are both WORD/PHRASE-CHOICE decisions (which language
a word is written in; whether a phrase collapses to initials) made against
lexicons keyed on Sinhala-script surface forms
(data/lexicon/codemix_wordbank.jsonl, data/lexicon/abbreviate_initialisms.jsonl)
-- not script/spelling decisions themselves. Transliteration converts all
remaining Sinhala to Latin script, so if either ran after it, their
Sinhala-keyed lexicons would have no Sinhala left to match against
downstream, and would silently never fire.

This was caught as a real bug during Phase 5 planning, not just a
theoretical concern: the order this module shipped with through Phase 4
(codemix -> transliteration -> misspell -> abbreviate) put abbreviate LAST,
after transliteration -- meaning abbreviate's entire Sinhala-bigram lexicon
would have found zero eligible occurrences in every compound-condition post,
ever. Fixed here, before compound generation ever ran for real, per the
plan's Stage 1. See eval/regression/pipeline_abbreviate_fires_in_compound.json
for the regression case that pins this down.

--- Real script mixing, not uniform full-Latin (user request) ---
The standalone `transliteration` condition deliberately romanizes 100% of
remaining Sinhala words (see src/noisers/transliteration.py's module
docstring) -- correct for THAT condition, but a real bilingual typist's
message is rarely uniform: some words stay in Sinhala script, some get
typed in Latin, within the same post. Compound uses transliteration's
`mixed_script_rate` parameter (default 0.0, so the standalone dataset is
completely unaffected -- verified byte-identical against all 20,000
already-shipped rows before this was wired in here) to romanize only a
FRACTION of remaining Sinhala words: MIXED_SCRIPT_RATE below, 20% at light
/ 40% at heavy (heavier severity = more total deviation from the clean
all-Sinhala baseline, consistent with what "severity" means everywhere
else in this project). A word produced by abbreviate's initials() is
always romanized regardless of this rate (never left half-Sinhala/
half-Latin within a single abbreviation pair) -- see
transliteration.py's `_is_abbreviation_fragment`.

--- Why misspell still runs last ---
Misspell is unique among the four in being SCRIPT-AWARE by design
(src/noisers/misspell.py's Channel A operates on Sinhala, Channel B on
Latin) specifically so it works correctly wherever it sits in the chain.
Running it after transliteration means it exercises mostly/only Channel B
in the compound condition (there's little to no Sinhala left by then) --
intentional, documented in misspell.py's own module docstring since before
this ordering fix, and unaffected by it.

--- Determinism and per-stage seeding ---
Each stage gets its own derived seed, zlib.crc32(f"{seed}:{stage_name}"),
so compound's internal randomness is independent of (not identical to)
each stage's STANDALONE per-vector seed for the same post -- expected: a
compound run is testing a different scenario (all four vectors interacting
in sequence), not replaying the same individual choices the standalone
per-vector datasets made. The overall seed passed to run() still fully
determines every stage's seed, so the whole chain is deterministic end to
end for a given (text, severity, seed).

--- compound_rate and n_substitutions ---
Each stage's own realised_noise_rate is already a well-calibrated,
severity-sensitive number (confirmed empirically for all four before this
module was written -- see LOG.md). compound_rate is the MEAN of the four
stages' rates from this specific chain run. A whole-text edit-distance
alternative was considered and rejected: transliteration's mandatory
script conversion would dominate that measure at both severities equally
and wash out the light/heavy distinction, whereas averaging the four
already-discriminating per-stage rates does not have that problem.

n_substitutions sums whatever codemix and abbreviate report in this chain
(the only two stages that do type-level forced selection -- see
schema.py's n_substitutions docstring); transliteration and misspell
don't populate it, contributing 0.
"""

from __future__ import annotations

import sys
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.noisers import abbreviate, codemix, misspell, transliteration  # noqa: E402

NOISER_ORDER = ("codemix", "abbreviate", "transliteration", "misspell")

# Stages whose module exposes a 3-tuple _apply() (also returns substitution
# detail) vs. a plain 2-tuple apply(). codemix's third element is a LIST of
# substituted word types (len() gives the count); abbreviate's is already an
# int count -- see each module's own _apply() docstring for why they differ.
_MODULES = {
    "codemix": codemix,
    "abbreviate": abbreviate,
    "transliteration": transliteration,
    "misspell": misspell,
}
_HAS_APPLY3 = {"codemix", "abbreviate"}

# Fraction of remaining Sinhala words transliteration romanizes in the
# compound chain (the rest stay in Sinhala script) -- see module docstring's
# "Real script mixing" section. Only ever passed to transliteration.apply()
# from here; the standalone transliteration condition never sees this.
MIXED_SCRIPT_RATE = {"light": 0.20, "heavy": 0.40}

# Measured once from a completed generation run (pooled mean compound_rate
# across train+test, 10,000 posts each severity, AFTER the mixed-script
# transliteration change -- see LOG.md's Phase 5 entries) -- a drift
# tripwire, not a natural-rate claim, same convention as codemix's and
# abbreviate's TARGET_NOISE_RATE. 98.8%/99.8% (light/heavy) of posts
# touched -- no longer a guaranteed 100% now that transliteration only
# romanizes a fraction of remaining Sinhala words (a very short post can
# get unlucky and have nothing altered by any of the four stages).
TARGET_NOISE_RATE = {"light": 0.1029, "heavy": 0.1851}


def _stage_seed(seed: int, stage_name: str) -> int:
    return zlib.crc32(f"{seed}:{stage_name}".encode("utf-8"))


def run(
    text: str, severity: str, seed: int, conditions: tuple[str, ...] = NOISER_ORDER
) -> tuple[str, float, int]:
    """Apply the requested noisers in `conditions` order (default
    NOISER_ORDER), each seeded deterministically from (seed, stage_name).

    Returns (final_text, compound_rate, n_substitutions):
      - compound_rate: mean of the per-stage realised_noise_rate values from
        this run (see module docstring).
      - n_substitutions: sum of codemix's and abbreviate's per-stage
        substitution counts in this run (0 from transliteration/misspell).

    Deterministic: the same (text, severity, seed, conditions, frozen
    lexicon files) always produces the same output.
    """
    current_text = text
    stage_rates: list[float] = []
    total_substitutions = 0

    for stage_name in conditions:
        module = _MODULES[stage_name]
        stage_seed = _stage_seed(seed, stage_name)
        if stage_name in _HAS_APPLY3:
            noisy_text, rate, detail = module._apply(current_text, severity, stage_seed)
            n = len(detail) if isinstance(detail, list) else detail
        elif stage_name == "transliteration":
            noisy_text, rate = module.apply(
                current_text, severity, stage_seed, mixed_script_rate=MIXED_SCRIPT_RATE[severity])
            n = 0
        else:
            noisy_text, rate = module.apply(current_text, severity, stage_seed)
            n = 0
        current_text = noisy_text
        stage_rates.append(rate)
        total_substitutions += n

    compound_rate = sum(stage_rates) / len(stage_rates) if stage_rates else 0.0
    return current_text, compound_rate, total_substitutions
