"""
Code-mixing noise vector: substitute a real, attested English word for a
Sinhala word, leaving the rest of the Sinhala matrix intact — e.g.
"ආණ්ඩුව අසාධාරණයි" -> "government එක අසාධාරණයි". This is a WORD-CHOICE
operation (which language a word is written in), deliberately orthogonal
to transliteration's SCRIPT/SPELLING operation — see src/pipeline.py for
why codemix therefore runs BEFORE transliteration in the compound order.

The lexicon (data/lexicon/codemix_lexicon.jsonl, built by
scripts/build_codemix_lexicon.py) is hand-curated, not automated: there is
no Sinhala-English dictionary anywhere in this repo, so every entry was
individually verified against real attested usage (three independent
evidence channels — see scripts/measure_codemix_rate.py) and against its
actual meaning (data/lexicon/codemix_rejected_candidates.md records what
was excluded and why, e.g. "වේසිගෙ" was rejected as a match for "website"
because it actually means "prostitute's" — a slur, not a translation).
Substitution keys are EXACT SURFACE FORMS observed in SOLD (Sinhala is
agglutinative; case lives in suffixes, e.g. "ආණ්ඩුවට" (to the government)
is a separate entry from "ආණ්ඩුව", not runtime-inflected) — this noiser
never does morphological analysis, only verified surface substitution,
exactly like src/noisers/transliteration.py's attested-spelling approach.

--- Why severity targets are small, and close together ---
Unlike spelling variance (which can touch almost any word), code-mixing is
inherently sparse: real Sinhala-English mixing concentrates in a specific,
limited vocabulary (tech/social/political loanwords, a handful of
translatable concepts), not general vocabulary. scripts/measure_codemix_rate.py
measured this directly: real Singlish runs ~1.0% English tokens (reference
corpus) to ~1.5-1.8% (SOLD itself, after stripping Twitter-scrape
artifacts). The lexicon built from that same measurement covers 1.74% of
SOLD's Sinhala word tokens — and a second, harder expansion pass (127 -> 210
entries) barely moved that number, because a rigorously-sourced lexicon and
the natural-rate measurement are reading off the same underlying behavior
in the same corpus; they converge, they don't stack. Coverage is therefore
a hard ceiling on the achievable REALISED rate (at attempt_probability=1.0,
the maximum possible mean realised_noise_rate is exactly the coverage
fraction), which rules out mirroring transliteration's targets (0.10/0.20)
outright — both would clip to the same ~1.74% ceiling and light/heavy would
be indistinguishable. TARGET_NOISE_RATE is instead set BELOW the ceiling
with real separation: light=0.010 (attempt_probability ~57%, close to the
reference corpus's own natural rate) and heavy=0.016 (~92% attempt
probability, close to but under the ceiling) — both small in absolute
terms because the real phenomenon is small, but heavy substitutes roughly
60% more words than light, a genuine, visible difference in output.
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

LEXICON_PATH = REPO_ROOT / "data" / "lexicon" / "codemix_lexicon.jsonl"

TARGET_NOISE_RATE = {"light": 0.010, "heavy": 0.016}

# Measured fraction of SOLD Sinhala word tokens with a lexicon entry (see
# docstring: 3026/173895, scripts/build_codemix_lexicon.py). Used to convert
# a target REALISED rate into the per-word attempt probability that
# actually produces it, exactly as src/noisers/transliteration.py does.
_COVERAGE = 0.0174
_ATTEMPT_PROBABILITY = {sev: min(1.0, rate / _COVERAGE) for sev, rate in TARGET_NOISE_RATE.items()}

GENERATOR_VERSION = "codemix-v1"

_lexicon_cache: dict[str, str] | None = None


def _load_lexicon() -> dict[str, str]:
    global _lexicon_cache
    if _lexicon_cache is None:
        if LEXICON_PATH.exists():
            with LEXICON_PATH.open(encoding="utf-8") as f:
                _lexicon_cache = {
                    row["sinhala"]: row["english"]
                    for row in (json.loads(line) for line in f if line.strip())
                }
        else:
            _lexicon_cache = {}
    return _lexicon_cache


def apply(text: str, severity: str, seed: int) -> tuple[str, float]:
    """Sinhala -> code-mixed text at the given severity ("light" | "heavy").

    Returns (noisy_text, realised_noise_rate). Deterministic: the same
    (text, severity, seed) always produces the same output — a single
    random.Random(seed) is consumed sequentially over words in
    left-to-right order, which is itself a deterministic function of the
    input text.
    """
    if severity not in TARGET_NOISE_RATE:
        raise ValueError(f"unknown severity {severity!r}, expected one of {list(TARGET_NOISE_RATE)}")

    attempt_probability = _ATTEMPT_PROBABILITY[severity]
    lexicon = _load_lexicon()
    rng = random.Random(seed)

    out_parts: list[str] = []
    n_words = 0
    n_altered = 0
    for is_sinhala, run in text_runs(text):
        if not is_sinhala:
            out_parts.append(run)
            continue
        n_words += 1
        substitution = lexicon.get(run)
        chosen = run
        if substitution is not None and rng.random() < attempt_probability:
            chosen = substitution
        if chosen != run:
            n_altered += 1
        out_parts.append(chosen)

    realised_noise_rate = (n_altered / n_words) if n_words else 0.0
    return "".join(out_parts), realised_noise_rate
