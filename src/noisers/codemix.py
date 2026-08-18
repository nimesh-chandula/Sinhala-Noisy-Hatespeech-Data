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
actually say this English word inside a Sinhala sentence? (see LOG.md:
across every mining pass tried, only ~5-7% of candidate words turned out to
be genuinely viable code-mix targets — forcing a substitution into every
post means some substitutions land on words that aren't natural swap
targets).

--- Round 4: evidence-based removal + attestation-aware selection ---
A reviewer objected that code-mixing places switches unnaturally. Tested
against SOLD's own naturally-occurring switches, that claim was REFUTED for
POSITION and LICENSING (in-place substitution inherits real switch sites by
construction — see the top of this docstring) but UPHELD for WORD CHOICE.
Two complementary fixes followed, each solving a different half of that:

  (A) REMOVAL (guarantees). ~97 entries whose English side is either an
      insult (translating an insult to English reads weaker, silently
      undermining the offensive signal the label depends on) or a bare
      English finite verb (Sinhala borrows verbs as
      "V + කරනවා/කරන්න/කරලා", never bare) were removed via
      data/lexicon/codemix_review_corrections.jsonl round 4 — the same
      append-only mechanism rounds 1-3 used. Both categories were confirmed,
      not just suspected: essentially zero natural attestation in SOLD.
      This is the only mechanism that can GUARANTEE a category never fires.

  (B) SELECTION (improvement, below). Even after removal, the surviving pool
      for a given post was still drawn uniformly at random -- no preference
      for words real Sinhala speakers are actually known to switch to over
      words that merely survived review. data/lexicon/codemix_attested_
      vocabulary.json (built by scripts/build_codemix_attestation.py) is an
      evidence index: every English headword with real evidence of being
      switched by a real Sinhala speaker, ranked "primary" (mined fresh from
      SOLD's own text -- the exact register this noiser is applied to),
      "secondary" (SOLD's "එක"-construction, the exact construction many
      bank entries encode), or "tertiary" (pooled loosely across corpora,
      noisy enough that a first draft of this selection change let "crazy"
      through as "attested" on a count of 2 with zero real intrasentential
      evidence -- tertiary is therefore excluded from the gate below and
      kept only as report-level context, not used to pick a word).

  Selection prefers plausible+attested words, falling back in three more
  steps only as each preference runs out (see _apply() below). This was
  validated by running BOTH algorithms across all 20,000 rows with the
  SAME seeds before being adopted here (scripts/compare_codemix_selection.py,
  data/lexicon/codemix_selection_comparison.md): evidence-backed picks
  nearly doubled (23.4% -> 41.6%) at ZERO coverage cost, and the position/
  licensing rebuttal was unaffected (JSD 0.0017 -> 0.0026, still << natural).

  IMPORTANT: (B) is a PREFERENCE, not a guarantee -- confirmed by that same
  comparison, checking WHY a removed-category word still got picked in the
  cases where it did: about half the time it was the ONLY reviewer-approved
  word available in that specific post, and preferring evidence can't help
  when there's nothing else to prefer. (A) and (B) are complementary, not
  substitutes; do not remove (A) on the assumption (B) makes it redundant.

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
ATTESTED_PATH = REPO_ROOT / "data" / "lexicon" / "codemix_attested_vocabulary.json"
ATTESTED_HASH_PATH = REPO_ROOT / "data" / "lexicon" / ".codemix_attested_vocabulary.sha256"

# Only these two evidence tiers gate selection -- see the module docstring's
# "Round 4" section for why "tertiary" (real, but too noisy) is excluded.
_ATTESTED_SELECTION_TIERS = frozenset({"primary", "secondary"})

# How many DISTINCT word TYPES are force-substituted per post, at each
# severity — capped at the number of eligible types actually present (never
# an error to have fewer than this available; see eval/invariants.py's
# check_codemix_substitution_spec for the exact contract).
_WORDS_PER_POST = {"light": 1, "heavy": 2}

# Re-measured and re-frozen after round 4 (97 entries removed -- 30
# affect-bearing, 67 bare-verb; plus the attestation-aware selection
# redesign). Pooled mean realised_noise_rate across train+test (10,000
# posts), wordbank sha256 f144730d... (4,021 entries), attested vocabulary
# sha256 2741e3c5... (2,641 entries, primary/secondary gate). 91.1%/92.2%
# (train/test) of posts had >=1 eligible word and were touched (down from
# 93.2%/93.9% pre-round-4 -- the expected coverage cost of the Tier 1+2
# removals; see data/lexicon/codemix_removals_round4.md). See the module
# docstring's "Why TARGET_NOISE_RATE is a tripwire, not a target" section --
# this is a drift tripwire, never a tuning target.
TARGET_NOISE_RATE = {"light": 0.0847, "heavy": 0.1112}


def _hash_suffix(path: Path) -> str:
    if path.exists():
        digest = path.read_text(encoding="utf-8").strip()
        return digest[:8] if digest else "unbuilt"
    return "unbuilt"


# GENERATOR_VERSION is stamped with BOTH frozen inputs' hashes: selection
# depends on the wordbank (which words are eligible at all) AND the attested
# vocabulary (which of those are preferred), so a rebuild of either must be
# visible in every output row's generator_version (golden rule 4).
GENERATOR_VERSION = f"codemix-v3+{_hash_suffix(WORDBANK_HASH_PATH)}+{_hash_suffix(ATTESTED_HASH_PATH)}"

_wordbank_cache: dict[str, dict] | None = None
_attested_cache: dict[str, dict] | None = None


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


def _load_attested_vocabulary() -> dict[str, dict]:
    """{headword_lowercase: {"tier": ..., "count": ..., "examples": [...]}},
    built by scripts/build_codemix_attestation.py. Same lazy-cache pattern as
    _load_wordbank(). Missing file -> {} (selection then behaves exactly like
    the pre-round-4 plausible/eligible-only algorithm, never an error)."""
    global _attested_cache
    if _attested_cache is None:
        if ATTESTED_PATH.exists():
            _attested_cache = json.loads(ATTESTED_PATH.read_text(encoding="utf-8"))
        else:
            _attested_cache = {}
    return _attested_cache


def _headword(english: str) -> str:
    return english.split()[0].lower().strip(".,") if english else ""


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
    attested = _load_attested_vocabulary()
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

    # Round 4: prefer words with real evidence of being switched by real
    # Sinhala speakers over words that merely survived review. Validated
    # directly against the current (pre-round-4) algorithm across all 20,000
    # SOLD rows before adoption -- see the module docstring's "Round 4"
    # section and scripts/compare_codemix_selection.py. Four-level priority,
    # first non-empty pool wins:
    #   1. plausible AND attested -- reviewed AND evidenced
    #   2. plausible               -- reviewed, no evidence found (this is
    #                                 the ENTIRE pre-round-4 algorithm)
    #   3. eligible AND attested   -- evidenced, not reviewer-approved
    #   4. eligible                -- final fallback, unchanged from before
    is_attested = lambda w: attested.get(_headword(wordbank[w]["english"]), {}).get("tier") in _ATTESTED_SELECTION_TIERS
    plausible_attested = [w for w in plausible if is_attested(w)]
    eligible_attested = [w for w in eligible if is_attested(w)]
    if plausible_attested:
        pool = plausible_attested
    elif plausible:
        pool = plausible
    elif eligible_attested:
        pool = eligible_attested
    else:
        pool = eligible

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
