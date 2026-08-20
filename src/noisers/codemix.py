"""
Code-mixing noise vector: substitute a real, attested English word or
phrase for a Sinhala word/span, leaving the rest of the Sinhala matrix
intact — e.g. "ආණ්ඩුව අසාධාරණයි" -> "government එක අසාධාරණයි". This is a
WORD-CHOICE operation (which language a word is written in), deliberately
orthogonal to transliteration's SCRIPT/SPELLING operation — see
src/pipeline.py for why codemix therefore runs BEFORE transliteration in
the compound order.

--- v2: forced per-post selection, on-demand-translated word bank ---
v1 ran an independent Bernoulli trial per eligible word; v2 fixed its
85.8%/79.7% untouched-row problem with forced type-level selection (light=1
type, heavy=2 types). See LOG.md "Phase 3 density expansion" for the full
history; superseded by round 4 (word choice) and round 5 (amount) below.

--- Round 4: evidence-based removal + attestation-aware selection ---
A reviewer objected that code-mixing places switches unnaturally. Tested
against SOLD's own naturally-occurring switches, that claim was REFUTED for
POSITION and LICENSING (in-place substitution inherits real switch sites by
construction) but UPHELD for WORD CHOICE. Two fixes: (A) ~97 wordbank
entries whose English side was an insult or a bare English finite verb were
removed via data/lexicon/codemix_review_corrections.jsonl (a hard
guarantee, checked by eval/invariants.py's check_codemix_no_affect_
substitution). (B) data/lexicon/codemix_attested_vocabulary.json ranks
every surviving English headword by real evidence of being switched by a
real Sinhala speaker ("primary"/"secondary"/"tertiary" tiers; only the
first two gate selection — see _ATTESTED_SELECTION_TIERS below). Full
detail: docs/research_documentation.md §9.10.

--- Round 5: distribution-sampled CMI, phrase-level insertion ---
A second reviewer objection: the AMOUNT of mixing (fixed at 1/2 word TYPES
regardless of post length or content) was as arbitrary as word choice had
been. Per Pratapa et al. (2018) — randomly generated code-mixed data with a
flat, ungrounded distribution measurably fails to help downstream models —
the fix samples a per-post target Code-Mixing Index (Das & Gambäck 2014)
from a DISTRIBUTION instead of forcing a fixed count, and reports CMI/SPF/
I-index (see eval/cmi.py) as the standard metrics instead of an in-house
noise rate.

Two distributions are used, both measured, neither assumed:
  light  = SOLD's OWN natural CMI distribution (mean ≈10.6), from
           data/lexicon/codemix_cmi_reference.json (scripts/measure_cmi_
           distribution.py). This is what SOLD's own natural code-mixing
           looks like — light is the "indistinguishable from real SOLD"
           condition, and reproduces it directly rather than approximating it.
  heavy  = this corpus's own ACHIEVABLE CEILING under the still-fully-
           intact reviewer-plausibility gate (mean ≈16.7, NOT the ~27.5
           mean the literature's Hinglish/YouTube corpora show), from
           data/lexicon/codemix_cmi_bands.json (scripts/freeze_codemix_
           cmi_bands.py). Reaching a literature-typical mean was tried
           three independent ways — translating far more single words,
           then mining+piloting+fully translating a phrase bank (2-3 word
           contiguous spans, data/lexicon/codemix_phrasebank.jsonl) — and
           all three converge on the same ~15-19 ceiling once every
           substitution must still pass the same plausibility gate round 4
           built. This is NOT a coverage shortfall to fix with more
           translation budget: most of a Sinhala sentence is closed-class
           grammar (pronouns, case particles, verb inflections) that Sinhala's
           status as the MATRIX LANGUAGE (Senaratne 2009's Matrix Language
           Frame analysis of Sinhala-English code-mixing) never allows to be
           replaced, and of what's left, only a minority of specific word/
           phrase choices are judged plausible. The gate was deliberately
           kept locked for heavy rather than relaxed to force a higher
           number — relaxing it to hit an unreachable target is exactly the
           unnatural-synthetic-distribution failure mode Pratapa (2018)
           warns about, and would reintroduce the very word-choice defect
           round 4 fixed. See docs/research_documentation.md §9.11 for the
           full defense, including why the achieved p75/p90 (23.5 / 33.3)
           already overlap the literature's 21-40 band wherever a post's
           own content genuinely supports it.

--- Round 7: eligibility-conditioned sampling (heavy only) ---
Round 5's sampling drew target_cmi blindly from the severity's bands
BEFORE checking whether the post had anything eligible -- discovered (by
inspecting data/outputs/codemix_low_cmi_samples.md) to double-count the
zero outcome for heavy: the 9.1% "(0,0)" band weight exists because 9.1%
of posts structurally have zero eligible units, but since EVERY post drew
from that same distribution regardless of its own content, a second,
independent ~9.1% chance of landing on 0 ALSO hit posts that had eligible
material sitting unused. Measured: predicted realised zero rate
0.091 + 0.909*0.091 = 17.6%, actual measured 18.2% -- confirms the
mechanism, not just a hunch.

Fixed by checking eligibility BEFORE sampling: a post with zero eligible
units gets target_cmi=0 directly (no draw -- matches its only possible
outcome anyway); a HEAVY post with >=1 eligible unit samples from the
band set with the (0,0) band excluded and the rest auto-renormalized
(_nonzero_bands()) -- this is not a new invented rule, it corrects a
mismatch between how heavy's bands were MEASURED (a ceiling computation,
where a post with eligible content can never have had a zero ceiling) and
how they were being SAMPLED FROM (blind to that same fact).

LIGHT IS DELIBERATELY LEFT UNCHANGED. Light's bands are a NATURAL-
OCCURRENCE measurement (SOLD's own real code-mixing rate), not a ceiling
-- their zero mass (86.7%) represents genuine human behaviour: most posts
that could easily be code-mixed simply weren't (SOLD's natural line-rate
is 13.3%, far below the ~91% of posts with *some* eligible word). Applying
the same conditioning to light would force mixing into every eligible
post and directly contradict the natural-rate finding light exists to
reproduce -- the asymmetry between severities here is intentional, not an
inconsistency.

--- The fill mechanism: budget, not a fixed count ---
_find_max_units() is a PURE function (no severity, no budget, no rng) that
greedily scans a post left-to-right and returns the maximal non-overlapping
set of switchable units, preferring the LONGEST available match at each
position (a plausible 3-word phrasebank span, else a plausible 2-word span,
else a single eligible word) — this maximal set IS the post's ceiling, and
is the exact function scripts/freeze_codemix_cmi_bands.py uses (unbounded)
to derive the heavy band weights above, so the measured ceiling and the
noiser's own runtime behavior can never drift apart.

_apply() samples a target CMI from the severity's frozen bands, converts it
to a token BUDGET, and fills from the maximal unit set: if the budget
covers everything, the full ceiling is used; otherwise the unit list is
seed-shuffled and packed greedily (accept if it fits, skip and keep trying
smaller units otherwise) rather than truncated in text order — this avoids
a systematic "front of the sentence is always noised, the tail rarely is"
bias a plain left-to-right cutoff would introduce.

This is a change from v2/round4's TYPE-level forced selection (a chosen
word TYPE had every occurrence in the post substituted) to OCCURRENCE-level
budget-driven selection (each occurrence, span or single, is its own unit)
— a deliberate consequence of budgeting in TOKENS, which is what CMI itself
counts. n_substitutions now counts UNITS chosen (spans + singles), not
distinct word types.

Word bank / phrase bank keys are EXACT SURFACE FORMS observed in SOLD
(Sinhala is agglutinative; case lives in suffixes) — this noiser never does
morphological analysis, only verified/translated surface substitution.

--- Why this stays deterministic ---
Translation happened ONCE, offline (see scripts/translate_codemix_
worklist.py) and its output was frozen into the wordbank/phrasebank before
this module ever runs. apply() is a pure function of (text, severity, seed,
the frozen files on disk) — no network call happens here, ever (golden
rule 5). GENERATOR_VERSION is stamped with every frozen input's own
SHA-256 (first 8 hex chars) so any rebuild is visible in every output row.
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
PHRASEBANK_PATH = REPO_ROOT / "data" / "lexicon" / "codemix_phrasebank.jsonl"
PHRASEBANK_HASH_PATH = REPO_ROOT / "data" / "lexicon" / ".codemix_phrasebank.sha256"
CMI_BANDS_PATH = REPO_ROOT / "data" / "lexicon" / "codemix_cmi_bands.json"
CMI_BANDS_HASH_PATH = REPO_ROOT / "data" / "lexicon" / ".codemix_cmi_bands.sha256"

# Only these two evidence tiers gate WORD selection -- see the module
# docstring's "Round 4" section for why "tertiary" (real, but too noisy) is
# excluded. Phrases have no attestation-tier concept of their own (round 5
# gates phrases purely on codemix_plausible -- see PHRASEBANK_PATH).
_ATTESTED_SELECTION_TIERS = frozenset({"primary", "secondary"})

# Measured once from a completed generation run (pooled mean
# realised_noise_rate across train+test, 10,000 posts each severity) --
# a drift TRIPWIRE for eval/harness.py's noise_rate_error, exactly as
# before round 5: realised_noise_rate keeps its old definition unchanged
# (n_altered_sinhala_words / n_sinhala_words -- see _apply()'s docstring),
# so this number is comparable across rounds even though the SELECTION
# mechanism underneath it changed completely. Not a natural-rate claim and
# not the same thing as target_cmi -- see the module docstring's "Round 5"
# section for the actual calibration target (CMI, checked by eval/cmi.py
# and eval/invariants.py's check_codemix_cmi_distribution).
TARGET_NOISE_RATE = {"light": 0.0138, "heavy": 0.1124}


def _hash_suffix(path: Path) -> str:
    if path.exists():
        digest = path.read_text(encoding="utf-8").strip()
        return digest[:8] if digest else "unbuilt"
    return "unbuilt"


# GENERATOR_VERSION is stamped with every frozen input's hash: which words
# are eligible (wordbank), which are preferred (attested), which spans
# exist (phrasebank), and how much mixing is targeted (cmi_bands) -- a
# rebuild of any one must be visible in every output row (golden rule 4).
GENERATOR_VERSION = (
    f"codemix-v4+{_hash_suffix(WORDBANK_HASH_PATH)}+{_hash_suffix(ATTESTED_HASH_PATH)}"
    f"+{_hash_suffix(PHRASEBANK_HASH_PATH)}+{_hash_suffix(CMI_BANDS_HASH_PATH)}"
)

_wordbank_cache: dict[str, dict] | None = None
_attested_cache: dict[str, dict] | None = None
_phrasebank2_cache: dict[tuple[str, str], dict] | None = None
_phrasebank3_cache: dict[tuple[str, str, str], dict] | None = None
_cmi_bands_cache: dict[str, list[tuple[float, float, float]]] | None = None


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
    built by scripts/build_codemix_attestation.py. Missing file -> {}
    (selection then behaves as if nothing were attested, never an error)."""
    global _attested_cache
    if _attested_cache is None:
        if ATTESTED_PATH.exists():
            _attested_cache = json.loads(ATTESTED_PATH.read_text(encoding="utf-8"))
        else:
            _attested_cache = {}
    return _attested_cache


def _load_phrasebank() -> tuple[dict[tuple[str, str], dict], dict[tuple[str, str, str], dict]]:
    """(bigram_bank, trigram_bank), keyed by the exact word tuple, built by
    scripts/build_codemix_phrasebank.py. ONLY codemix_plausible=true rows
    are indexed here -- round 5 deliberately keeps the plausibility gate
    locked for phrases at BOTH severities (see the module docstring's
    "Round 5" section for why relaxing it to hit a higher CMI number was
    rejected), so a non-plausible phrasebank row is never reachable through
    this loader at all, not merely deprioritized."""
    global _phrasebank2_cache, _phrasebank3_cache
    if _phrasebank2_cache is None:
        bank2: dict[tuple[str, str], dict] = {}
        bank3: dict[tuple[str, str, str], dict] = {}
        if PHRASEBANK_PATH.exists():
            with PHRASEBANK_PATH.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    if not row["codemix_plausible"]:
                        continue
                    words = tuple(row["words"])
                    if len(words) == 2:
                        bank2[words] = row
                    elif len(words) == 3:
                        bank3[words] = row
        _phrasebank2_cache, _phrasebank3_cache = bank2, bank3
    return _phrasebank2_cache, _phrasebank3_cache


def _load_cmi_bands() -> dict[str, list[tuple[float, float, float]]]:
    """{severity: [(lo, hi, weight), ...]}, frozen by scripts/freeze_
    codemix_cmi_bands.py -- see that script and the module docstring's
    "Round 5" section for how light (SOLD-natural) and heavy (this corpus's
    measured achievable ceiling) were derived. Missing file is a hard
    error, unlike the other loaders: unlike an empty wordbank (which just
    means nothing is eligible, a valid state), there is no safe default
    band shape to fall back to -- generation must not silently invent one."""
    global _cmi_bands_cache
    if _cmi_bands_cache is None:
        if not CMI_BANDS_PATH.exists():
            raise FileNotFoundError(
                f"{CMI_BANDS_PATH} not found -- run scripts/freeze_codemix_cmi_bands.py first "
                "(golden rule 1: the calibration target must exist before generation uses it)"
            )
        raw = json.loads(CMI_BANDS_PATH.read_text(encoding="utf-8"))
        _cmi_bands_cache = {
            severity: [(b["lo"], b["hi"], b["weight"]) for b in bands]
            for severity, bands in raw["bands"].items()
        }
    return _cmi_bands_cache


def _headword(english: str) -> str:
    return english.split()[0].lower().strip(".,") if english else ""


def _single_word_pool(sinhala_words: set[str], wordbank: dict, attested: dict) -> list[str]:
    """Round 4's 4-level priority, unchanged: the first non-empty pool wins.
        1. plausible AND attested -- reviewed AND evidenced
        2. plausible               -- reviewed, no evidence found (the
                                       entire pre-round-4 algorithm)
        3. eligible AND attested   -- evidenced, not reviewer-approved
        4. eligible                -- final fallback
    Returns a SORTED list of word forms (sorted() is a correctness
    requirement -- Python randomises str hashing per process, so building
    this from an unsorted set would break determinism across separate runs
    of the same (text, severity, seed); see check_determinism's docstring
    in eval/harness.py for why that specific bug is invisible to a
    same-process comparison)."""
    eligible = sorted({w for w in sinhala_words if w in wordbank})
    plausible = [w for w in eligible if wordbank[w]["codemix_plausible"]]
    is_attested = lambda w: attested.get(_headword(wordbank[w]["english"]), {}).get("tier") in _ATTESTED_SELECTION_TIERS
    plausible_attested = [w for w in plausible if is_attested(w)]
    eligible_attested = [w for w in eligible if is_attested(w)]
    if plausible_attested:
        return plausible_attested
    if plausible:
        return plausible
    if eligible_attested:
        return eligible_attested
    return eligible


def _find_max_units(text: str) -> tuple[list[tuple[bool, str]], list[dict]]:
    """PURE function: no severity, no budget, no rng -- a single greedy
    left-to-right pass over `text`'s grapheme-run structure, preferring the
    LONGEST available match at each not-yet-consumed Sinhala run: a
    plausible 3-word phrasebank span, else a plausible 2-word span, else a
    single word from _single_word_pool(). The resulting non-overlapping
    unit list, taken in FULL, is this post's CEILING -- the exact quantity
    scripts/freeze_codemix_cmi_bands.py measures (unbounded) to derive the
    heavy band weights, so "how the ceiling was measured" and "how
    generation actually behaves" can never drift apart.

    Returns (runs, units) where runs is text_runs(text) (needed by the
    caller to rebuild output text) and units is
    [{"start": run_index, "n_words": 2|3|1, "text": run text at start (for
    singles) or None, "entry": phrasebank row or None}], in left-to-right
    text order."""
    runs = text_runs(text)
    n = len(runs)
    sinhala_words = {run for is_sinhala, run in runs if is_sinhala}
    wordbank = _load_wordbank()
    attested = _load_attested_vocabulary()
    bank2, bank3 = _load_phrasebank()
    single_pool = set(_single_word_pool(sinhala_words, wordbank, attested))

    consumed = [False] * n
    units: list[dict] = []
    for i in range(n):
        is_sin, word = runs[i]
        if not is_sin or consumed[i]:
            continue
        if i + 4 < n:
            is_c1, c1 = runs[i + 1]
            is_sb, b = runs[i + 2]
            is_c2, c2 = runs[i + 3]
            is_sc, c = runs[i + 4]
            if is_sb and is_sc and not is_c1 and c1.strip() == "" and not is_c2 and c2.strip() == "":
                entry = bank3.get((word, b, c))
                if entry is not None:
                    consumed[i] = consumed[i + 2] = consumed[i + 4] = True
                    units.append({"start": i, "n_words": 3, "text": None, "entry": entry})
                    continue
        if i + 2 < n:
            is_c1, c1 = runs[i + 1]
            is_sb, b = runs[i + 2]
            if is_sb and not is_c1 and c1.strip() == "":
                entry = bank2.get((word, b))
                if entry is not None:
                    consumed[i] = consumed[i + 2] = True
                    units.append({"start": i, "n_words": 2, "text": None, "entry": entry})
                    continue
        if word in single_pool:
            consumed[i] = True
            units.append({"start": i, "n_words": 1, "text": word, "entry": None})
    return runs, units


def _sample_target_cmi(bands: list[tuple[float, float, float]], rng: random.Random) -> float:
    """Weighted band pick, then uniform draw within the picked band -- the
    same two-step scheme used throughout this repo's distribution-sampled
    values."""
    total_weight = sum(w for _lo, _hi, w in bands)
    r = rng.uniform(0, total_weight)
    cum = 0.0
    for lo, hi, w in bands:
        cum += w
        if r <= cum:
            return rng.uniform(lo, hi)
    lo, hi, _w = bands[-1]
    return rng.uniform(lo, hi)


def _nonzero_bands(bands: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    """Drop the (0, 0) band. `_sample_target_cmi` computes its own total
    weight from whatever list it's handed, so removing one entry is
    sufficient to renormalize the rest -- no separate rescaling step
    needed. Round 7's heavy-only eligibility conditioning -- see the
    module docstring's "Round 7" section."""
    return [(lo, hi, w) for lo, hi, w in bands if not (lo == 0 and hi == 0)]


def _pack_units_to_budget(units: list[dict], budget: int, target_cmi: float, rng: random.Random) -> list[dict]:
    """If the full unit set already fits the budget, use all of it
    (deterministic, no rng draw). Otherwise seed-shuffle a COPY of the unit
    list and greedily accept units that still fit, skipping ones that
    don't (so a later smaller unit can still fit after a larger one is
    skipped) -- shuffling avoids a plain left-to-right truncation's
    systematic bias toward noising the front of a sentence and leaving the
    tail untouched.

    --- The budget=0-but-target>0 fallback ---
    `budget = round(target_cmi/100 * n_words)` rounds a small positive
    target down to a literal 0 whenever the post is short relative to the
    target (e.g. target_cmi=3 on a 15-word post rounds to 0) -- discovered
    empirically after the first real generation run: mean realised CMI came
    out at roughly HALF the mean target_cmi, with 2,096/10,000 heavy rows
    landing on a positive target_cmi but zero actual substitution. A
    positive target_cmi is a genuine (if small) mixing intent, not "maybe
    nothing" depending on unit-size luck -- so if packing would otherwise
    leave a positive-target post completely untouched, fall back to the
    SMALLEST available unit (a small, bounded overshoot past budget) rather
    than silently realising 0. This does not apply when target_cmi==0
    exactly (the light severity's explicit "stay monolingual" band, or a
    heavy post whose ceiling band draw was legitimately the 0 band) --
    that must still mean truly untouched."""
    total = sum(u["n_words"] for u in units)
    if total <= budget:
        return units
    shuffled = units[:]
    rng.shuffle(shuffled)
    chosen: list[dict] = []
    running = 0
    for u in shuffled:
        if running + u["n_words"] <= budget:
            chosen.append(u)
            running += u["n_words"]
    if not chosen and target_cmi > 0 and units:
        chosen = [min(units, key=lambda u: u["n_words"])]
    # restore left-to-right text order for deterministic output assembly
    chosen.sort(key=lambda u: u["start"])
    return chosen


def _apply(text: str, severity: str, seed: int) -> tuple[str, float, list[dict], float]:
    """Core implementation, shared by apply() (2-tuple) and
    generate_codemix.py's row-writing loop (which also needs n_substitutions
    and target_cmi).

    Returns (noisy_text, realised_noise_rate, chosen_units, target_cmi).
    realised_noise_rate keeps its EXISTING definition (n_altered_sinhala_
    words / n_sinhala_words) unchanged from v2/round4 -- see
    src/schema.py and eval/harness.py's noise_rate_error, which both still
    consume it as-is. CMI itself (the new, literature-standard metric) is
    NOT computed here -- eval/cmi.py recomputes it independently from the
    finished noisy_text, the same way it measures SOLD's natural rate, so
    the reported metric can never simply echo back this module's own
    internal bookkeeping.
    """
    bands_by_severity = _load_cmi_bands()
    if severity not in bands_by_severity:
        raise ValueError(f"unknown severity {severity!r}, expected one of {list(bands_by_severity)}")

    rng = random.Random(seed)
    runs, units = _find_max_units(text)
    n_words = sum(1 for is_sinhala, _run in runs if is_sinhala)

    if not units:
        # No eligible unit at all -- the only possible outcome is 0, so
        # skip the draw entirely rather than sample something that packing
        # would discard anyway (see the module docstring's "Round 7" note).
        target_cmi = 0.0
    elif severity == "heavy":
        # Round 7: condition on eligibility for heavy only -- see the
        # module docstring's "Round 7" section for why light is exempt.
        target_cmi = _sample_target_cmi(_nonzero_bands(bands_by_severity["heavy"]), rng)
    else:
        target_cmi = _sample_target_cmi(bands_by_severity[severity], rng)

    budget = round(target_cmi / 100 * n_words) if n_words else 0
    chosen_units = _pack_units_to_budget(units, budget, target_cmi, rng)

    chosen_by_start = {u["start"]: u for u in chosen_units}
    out_parts: list[str] = []
    n_altered = 0
    i = 0
    while i < len(runs):
        unit = chosen_by_start.get(i)
        if unit is None:
            out_parts.append(runs[i][1])
            i += 1
            continue
        if unit["entry"] is not None:
            out_parts.append(unit["entry"]["english"])
            n_altered += unit["n_words"]
            # skip the consumed run span: n_words spans (n_words-1) connector
            # runs between them, i.e. 2*n_words - 1 runs total starting at i
            i += 2 * unit["n_words"] - 1
        else:
            wordbank = _load_wordbank()
            out_parts.append(wordbank[unit["text"]]["english"])
            n_altered += 1
            i += 1

    realised_noise_rate = (n_altered / n_words) if n_words else 0.0
    return "".join(out_parts), realised_noise_rate, chosen_units, target_cmi


def apply(text: str, severity: str, seed: int) -> tuple[str, float]:
    """Sinhala -> code-mixed text at the given severity ("light" | "heavy").

    Returns (noisy_text, realised_noise_rate). Deterministic: the same
    (text, severity, seed, frozen lexicon files) always produces the same
    output. Thin 2-tuple wrapper around _apply() -- see eval/harness.py's
    generic noiser-case runner and check_determinism, which both unpack
    exactly 2 values from every noiser's apply().
    """
    noisy_text, realised_noise_rate, _chosen_units, _target_cmi = _apply(text, severity, seed)
    return noisy_text, realised_noise_rate
