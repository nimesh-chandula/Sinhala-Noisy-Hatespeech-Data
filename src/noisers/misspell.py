"""
Misspelling noise vector: two script-aware channels that model how real
typos actually happen, rather than random grapheme-level noise.

--- Channel A: Sinhala script -- IME phonetic-collision substitution ---
Most Sinhala typing today goes through a phonetic IME on an English
keyboard (Helakuru, Google Sinhala Input, etc.): the typist types a roman
spelling and the keyboard resolves it to a Sinhala grapheme cluster. Where
that mapping is genuinely ambiguous, the IME's choice is not always the one
the typist meant -- type "na" and you may get න when you wanted ණ. So two
Sinhala grapheme clusters are treated as confusable exactly when they
romanize to the SAME string under the Phase-1-winning backend
(src/romanizers/aksharamukha.py's romanize_colloquial) -- derived from SOLD
itself by scripts/build_misspell_confusions.py, not hand-guessed. Measured:
767 distinct SOLD grapheme clusters -> 130 confusion sets (freq>=5,
ZWJ/ZWNJ artifacts excluded), covering 90.0% of Sinhala cluster tokens,
reviewed and approved as-is (see LOG.md's Phase 4a entries and
data/lexicon/misspell_confusions_review.md). Each substitution is exactly
one grapheme cluster swapped for another member of its confusion set --
never a partial/mid-cluster edit -- so cluster count is always preserved
and golden rule 3 (never split mid-syllable) holds structurally.

Attestation: "prefer attested, allow unattested" (mirrors codemix's
codemix_plausible prefer/fallback design in src/noisers/codemix.py). For a
candidate substitution, the resulting WORD is checked against
data/lexicon/misspell_attested_vocab.txt (SOLD's own vocabulary unioned
with the ~451K distinct words in the Swa-Bhasha word list, frozen by the
same build script). If >=1 candidate produces an attested word, only those
are offered; otherwise every member of the confusion set is fair game --
attested-only would cap coverage at ~25% of SOLD word types, and a typo is
by definition often not a real word anyway.

--- Channel B: Latin/Singlish script -- rule-based typo generator ---
Not lexicon-based (unlike Channel A): geminate consonant drop/add
("kanna"<->"kana"), vowel length ("a"<->"aa", "i"<->"ee", "u"<->"oo"),
aspiration ("th"<->"t", "kh"<->"k", ...), sibilant ("s"<->"sh"), w/v swap,
final -e/-a, and a deliberately LOW-WEIGHT single-character QWERTY-adjacent
slip. This channel exists so the noiser stays script-aware and correct once
misspell runs after transliteration in the compound pipeline
(src/pipeline.py's NOISER_ORDER) -- it is NOT exercised by this stage's own
generation, since the standalone `misspell` condition's input is always
clean Sinhala SOLD text (see scripts/generate_misspell.py), so Channel B
never fires there except on any pre-existing Latin word already sitting
inside a SOLD post (usernames, English loanwords typed in Latin, etc.) --
left unprotected deliberately, since a realistic misspelled variant of a
mixed-script post plausibly misspells the Latin portions too.

ORTHOGONALITY RULE (load-bearing): any Latin form appearing anywhere in
data/lexicon/word_variants.jsonl's romanization lists is an ATTESTED
alternate spelling -- that is the transliteration vector's severity lever
(src/noisers/transliteration.py). Channel B must never produce one of
those forms, or the two vectors would measure the same thing under two
names. Every candidate is checked against the union of all attested
romanizations and dropped if it matches.

--- Severity ---
Per-word attempt probability, coverage-corrected exactly like
transliteration.py's _ATTEMPT_PROBABILITY: probability = target_rate /
coverage, so the REALISED rate (what noise_rate_error actually checks)
lands on target. _COVERAGE_A = 0.9942 was measured once over SOLD
train+test (fraction of Sinhala word TOKENS containing >=1 confusable
cluster) -- there is no real coverage ceiling here, unlike codemix v1's
1.74%.

--- Determinism ---
A single random.Random(seed) is consumed sequentially over words in
left-to-right order (same discipline as every other noiser here). Every
candidate list this module builds is either a plain list read directly
from a frozen JSONL array (file/insertion order, never touched by
PYTHONHASHSEED) or built by iterating that same fixed order -- unlike
codemix's original bug (see src/noisers/codemix.py's docstring), nothing
here is ever sampled from a `set`, so there is no cross-process
hash-randomization risk to guard against with an explicit sort. Rule-type
selection within Channel B uses random.Random.choices() (weights + a
single random() draw), which is likewise pure arithmetic.
"""

from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import clusters, text_runs  # noqa: E402

LEXICON_DIR = REPO_ROOT / "data" / "lexicon"
CONFUSIONS_PATH = LEXICON_DIR / "misspell_confusions.jsonl"
CONFUSIONS_HASH_PATH = LEXICON_DIR / ".misspell_confusions.sha256"
ATTESTED_VOCAB_PATH = LEXICON_DIR / "misspell_attested_vocab.txt"
WORD_VARIANTS_PATH = LEXICON_DIR / "word_variants.jsonl"

TARGET_NOISE_RATE = {"light": 0.05, "heavy": 0.15}

# Measured once over SOLD train+test: fraction of Sinhala word TOKENS
# containing >=1 grapheme cluster that's a member of some confusion set
# (see module docstring). Used to convert a target REALISED rate into the
# per-word attempt probability that actually produces it, exactly like
# src/noisers/transliteration.py's _COVERAGE.
_COVERAGE_A = 0.9942
_ATTEMPT_PROBABILITY = {sev: min(1.0, rate / _COVERAGE_A) for sev, rate in TARGET_NOISE_RATE.items()}


def _confusions_version_suffix() -> str:
    if CONFUSIONS_HASH_PATH.exists():
        digest = CONFUSIONS_HASH_PATH.read_text(encoding="utf-8").strip()
        return digest[:8] if digest else "unbuilt"
    return "unbuilt"


GENERATOR_VERSION = f"misspell-v1+{_confusions_version_suffix()}"

_confusions_cache: dict[str, list[str]] | None = None
_attested_vocab_cache: set[str] | None = None
_word_variants_latin_cache: set[str] | None = None


def _load_confusions() -> dict[str, list[str]]:
    """{cluster: [other members of its confusion set, frequency-sorted]}."""
    global _confusions_cache
    if _confusions_cache is None:
        mapping: dict[str, list[str]] = {}
        if CONFUSIONS_PATH.exists():
            with CONFUSIONS_PATH.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    row = json.loads(line)
                    members = row["members"]
                    for c in members:
                        mapping[c] = [m for m in members if m != c]
        _confusions_cache = mapping
    return _confusions_cache


def _load_attested_vocab() -> set[str]:
    global _attested_vocab_cache
    if _attested_vocab_cache is None:
        if ATTESTED_VOCAB_PATH.exists():
            with ATTESTED_VOCAB_PATH.open(encoding="utf-8") as f:
                _attested_vocab_cache = {line.strip() for line in f if line.strip()}
        else:
            _attested_vocab_cache = set()
    return _attested_vocab_cache


def _load_word_variants_latin() -> set[str]:
    """Union of every attested romanization variant across
    data/lexicon/word_variants.jsonl, regardless of which Sinhala word it
    belongs to -- Channel B's orthogonality exclusion set (see module
    docstring)."""
    global _word_variants_latin_cache
    if _word_variants_latin_cache is None:
        variants: set[str] = set()
        if WORD_VARIANTS_PATH.exists():
            with WORD_VARIANTS_PATH.open(encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    variants.update(json.loads(line)["romanizations"])
        _word_variants_latin_cache = variants
    return _word_variants_latin_cache


# ---------------------------------------------------------------------------
# Channel A: Sinhala IME phonetic-collision substitution
# ---------------------------------------------------------------------------

def _apply_channel_a(
    word: str, rng: random.Random, confusions: dict[str, list[str]], attested_vocab: set[str]
) -> tuple[str, bool]:
    cs = clusters(word)
    eligible_positions = [i for i, c in enumerate(cs) if c in confusions]
    if not eligible_positions:
        return word, False

    pos = rng.choice(eligible_positions)
    original = cs[pos]
    members = confusions[original]

    attested = []
    for cand in members:
        candidate_word = "".join(cs[:pos] + [cand] + cs[pos + 1:])
        if candidate_word in attested_vocab:
            attested.append(cand)
    pool = attested if attested else members

    chosen = rng.choice(pool)
    new_word = "".join(cs[:pos] + [chosen] + cs[pos + 1:])
    return new_word, True


# ---------------------------------------------------------------------------
# Channel B: Latin/Singlish rule-based typo generator
# ---------------------------------------------------------------------------

_CONSONANTS = set("bcdfghjklmnpqrstvwxyz")
_VOWEL_LENGTH_PAIRS = [("aa", "a"), ("ee", "i"), ("oo", "u")]
_ASPIRATION_PAIRS = [("th", "t"), ("kh", "k"), ("ph", "p"), ("gh", "g"), ("bh", "b"), ("dh", "d")]
_SIBILANT_PAIRS = [("sh", "s")]
_WV_PAIR = [("w", "v")]
_QWERTY_ADJACENT = {
    "q": "wa", "w": "qe", "e": "wr", "r": "et", "t": "ry", "y": "tu", "u": "yi", "i": "uo",
    "o": "ip", "p": "ol", "a": "sq", "s": "ad", "d": "sf", "f": "dg", "g": "fh", "h": "gj",
    "j": "hk", "k": "jl", "l": "k", "z": "x", "x": "zc", "c": "xv", "v": "cb", "b": "vn",
    "n": "bm", "m": "n",
}


def _double_drop_candidates(word: str) -> list[str]:
    m = re.search(r"([a-z])\1", word)
    if not m:
        return []
    i = m.start()
    return [word[:i] + word[i] + word[i + 2:]]


def _double_add_candidates(word: str) -> list[str]:
    for i in range(1, len(word)):
        ch = word[i]
        if ch in _CONSONANTS and word[i - 1] != ch and (i + 1 >= len(word) or word[i + 1] != ch):
            return [word[:i] + ch + word[i:]]
    return []


def _swap_pairs(word: str, pairs: list[tuple[str, str]]) -> list[str]:
    """For each (long, short) pair: contract the first `long` occurrence to
    `short`, and/or expand the first `short` occurrence (that isn't already
    part of a `long` match) to `long`. Handles both directions from a single
    pair table (e.g. "th"/"t", "w"/"v")."""
    out = []
    for long, short in pairs:
        i = word.find(long)
        if i != -1:
            out.append(word[:i] + short + word[i + len(long):])
        j = 0
        while True:
            j = word.find(short, j)
            if j == -1:
                break
            if word[j:j + len(long)] != long:
                out.append(word[:j] + long + word[j + len(short):])
                break
            j += 1
    return out


def _final_vowel_candidates(word: str) -> list[str]:
    if len(word) < 2:
        return []
    if word.endswith("e"):
        return [word[:-1] + "a"]
    if word.endswith("a"):
        return [word[:-1] + "e"]
    return []


def _qwerty_candidates(word: str) -> list[str]:
    out = []
    for i in range(1, len(word)):
        adj = _QWERTY_ADJACENT.get(word[i])
        if not adj:
            continue
        for a in adj:
            out.append(word[:i] + a + word[i + 1:])
    return out


# (rule_name, candidate_fn, weight) -- weight controls how often this rule
# type is picked among those with >=1 viable candidate for a given word.
# QWERTY is deliberately low-weight: real typos are dominated by phonetic/
# spelling confusion, not raw fat-finger slips, for a phonetic-IME typist.
_RULE_TYPES: list[tuple[str, "callable", int]] = [
    ("geminate_drop", _double_drop_candidates, 3),
    ("geminate_add", _double_add_candidates, 3),
    ("vowel_length", lambda w: _swap_pairs(w, _VOWEL_LENGTH_PAIRS), 3),
    ("aspiration", lambda w: _swap_pairs(w, _ASPIRATION_PAIRS), 2),
    ("sibilant", lambda w: _swap_pairs(w, _SIBILANT_PAIRS), 2),
    ("w_v", lambda w: _swap_pairs(w, _WV_PAIR), 2),
    ("final_vowel", _final_vowel_candidates, 2),
    ("qwerty_adjacent", _qwerty_candidates, 1),
]


def _apply_channel_b(word: str, rng: random.Random, excluded_latin: set[str]) -> tuple[str, bool]:
    if len(word) < 3 or not word.isalpha() or not word.isascii() or not word.islower():
        return word, False

    applicable: dict[str, list[str]] = {}
    weights: dict[str, int] = {}
    for name, fn, weight in _RULE_TYPES:
        cands = [c for c in fn(word) if c != word and c not in excluded_latin]
        if cands:
            applicable[name] = cands
            weights[name] = weight
    if not applicable:
        return word, False

    names = sorted(applicable)
    chosen_rule = rng.choices(names, weights=[weights[n] for n in names], k=1)[0]
    chosen = rng.choice(sorted(applicable[chosen_rule]))
    return chosen, True


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

_LATIN_WORD_RE = re.compile(r"[A-Za-z]+")


def apply(text: str, severity: str, seed: int) -> tuple[str, float]:
    """Sinhala/Singlish -> misspelled text at the given severity
    ("light" | "heavy"). Returns (noisy_text, realised_noise_rate).

    Deterministic: the same (text, severity, seed, frozen lexicon files)
    always produces the same output. Dispatches per grapheme-cluster run
    (src.graphemes.text_runs) so Sinhala content goes through Channel A and
    Latin content through Channel B in a single pass -- see module
    docstring for why both channels live in one noiser.
    """
    if severity not in TARGET_NOISE_RATE:
        raise ValueError(f"unknown severity {severity!r}, expected one of {list(TARGET_NOISE_RATE)}")

    attempt_probability = _ATTEMPT_PROBABILITY[severity]
    confusions = _load_confusions()
    attested_vocab = _load_attested_vocab()
    excluded_latin = _load_word_variants_latin()
    rng = random.Random(seed)

    out_parts: list[str] = []
    n_words = 0
    n_altered = 0

    for is_sinhala, run in text_runs(text):
        if is_sinhala:
            n_words += 1
            if rng.random() < attempt_probability:
                new_word, changed = _apply_channel_a(run, rng, confusions, attested_vocab)
                out_parts.append(new_word)
                n_altered += changed
            else:
                out_parts.append(run)
            continue

        # Non-Sinhala run: may hold several Latin words plus punctuation/
        # spaces/digits (e.g. after transliteration, or pre-existing Latin
        # content in a SOLD post) -- split out just the alphabetic pieces
        # for Channel B and pass everything else through unchanged.
        last_end = 0
        for m in _LATIN_WORD_RE.finditer(run):
            out_parts.append(run[last_end:m.start()])
            piece = m.group(0)
            n_words += 1
            if rng.random() < attempt_probability:
                new_piece, changed = _apply_channel_b(piece, rng, excluded_latin)
                out_parts.append(new_piece)
                n_altered += changed
            else:
                out_parts.append(piece)
            last_end = m.end()
        out_parts.append(run[last_end:])

    realised_noise_rate = (n_altered / n_words) if n_words else 0.0
    return "".join(out_parts), realised_noise_rate
