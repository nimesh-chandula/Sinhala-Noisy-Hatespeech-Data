"""
Realism score: how close generated Singlish is to REAL Singlish.
Measured as Jensen-Shannon divergence between character 3-gram distributions.
Lower is better. This is the soft target Phase 2 optimizes (30% reduction
from the plain-romanization baseline).

Reference corpus of real Singlish lives in data/reference/reference_singlish.txt
(the romanized side of held-out Swa-Bhasha sentence pairs, disjoint from the
CER gold set — see scripts/fetch_data.py). It contains largely unpunctuated,
lowercase-mixed real social-media text, so both sides of every JSD comparison
are passed through the SAME `normalize_v2` first: comparing raw generated
text (which may carry punctuation/casing a real romanizer stub doesn't) against
raw reference text would measure normalization mismatch, not realism.

--- normalize_v2 (Phase 2 finding) ---
SOLD anonymizes user mentions and links to literal
"@USER"/"URL" placeholder tokens (found in ~60%/~10% of sampled posts).
These are SOLD's own annotation artifact, not organic text, and the Swa-Bhasha
reference corpus was never anonymized this way — so their trigrams (e.g.
"use", "ser", "er ") were the single largest source of divergence, reflecting
a corpus-processing mismatch rather than unrealistic romanization. v2 strips
them before scoring ONLY — this never touches the actual generated dataset
written to data/outputs/, since a downstream hate-speech classifier trained
on SOLD expects those tokens verbatim.
"""

from __future__ import annotations

import json
import math
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

REFERENCE_DIR = REPO_ROOT / "data" / "reference"
REFERENCE_PATH = REFERENCE_DIR / "reference_singlish.txt"

NORMALIZE_VERSION = "v2"
_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")
_USER_RE = re.compile(r"@USER", flags=re.IGNORECASE)
_URL_RE = re.compile(r"\bURL\b")


def normalize_v2(text: str) -> str:
    """Strip SOLD's @USER/URL anonymization placeholders, lowercase, strip
    punctuation, collapse whitespace.

    Applied identically to reference and generated text before scoring.
    Version-stamped (see NORMALIZE_VERSION) because changing this function
    changes every realism_jsd number — later phases need to know which
    normalization a stored report used. Scoring-only (see module docstring)
    — never applied to the actual generated dataset.
    """
    text = _USER_RE.sub(" ", text)
    text = _URL_RE.sub(" ", text)
    text = text.lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def char_ngrams(text: str, n: int = 3) -> Counter:
    text = f" {text} "
    return Counter(text[i:i + n] for i in range(len(text) - n + 1))


def _dist(texts: list[str], n: int = 3) -> dict[str, float]:
    total: Counter = Counter()
    for t in texts:
        total.update(char_ngrams(t, n))
    s = sum(total.values()) or 1
    return {k: v / s for k, v in total.items()}


def jensen_shannon(p: dict[str, float], q: dict[str, float]) -> float:
    keys = set(p) | set(q)
    m = {k: 0.5 * (p.get(k, 0.0) + q.get(k, 0.0)) for k in keys}

    def kl(a, b):
        out = 0.0
        for k in keys:
            ak = a.get(k, 0.0)
            if ak > 0 and b.get(k, 0.0) > 0:
                out += ak * math.log2(ak / b[k])
        return out

    return 0.5 * kl(p, m) + 0.5 * kl(q, m)


def load_reference() -> list[str]:
    """Real Singlish lines from data/reference/reference_singlish.txt."""
    if not REFERENCE_PATH.exists():
        return []
    with REFERENCE_PATH.open(encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


OUTPUTS_DIR = REPO_ROOT / "data" / "outputs"
SPLITS = ("train", "test")
SEVERITIES = ("light", "heavy")


def load_generated_by_condition() -> dict[str, list[str]]:
    """{condition_name: [generated_singlish, ...]} read from data/outputs/.

    Pools both splits' noisy_text together per condition/severity (e.g.
    "transliteration_heavy") — this is a read-only aggregate text statistic,
    not a data-provenance operation, so it doesn't violate the rule that
    train/test rows themselves are never merged or cross-written on disk.
    Empty until a condition's output files exist (Phase 2+).
    """
    out: dict[str, list[str]] = {}
    for severity in SEVERITIES:
        texts = []
        for split in SPLITS:
            path = OUTPUTS_DIR / split / f"transliteration_{severity}.jsonl"
            if not path.exists():
                continue
            with path.open(encoding="utf-8") as f:
                texts.extend(json.loads(line)["noisy_text"] for line in f if line.strip())
        if texts:
            out[f"transliteration_{severity}"] = texts
    return out


def baseline_jsd(reference: list[str], seed: int = 1337) -> float | None:
    """JSD of the reference corpus against a random split-half of itself.

    Not zero — 3-gram distributions from finite samples never match exactly.
    This is the realistic FLOOR: no generated condition should be expected to
    score lower than this, and Phase 2's "30% reduction from baseline" target
    is only meaningful measured against something like this floor rather than
    against zero.
    """
    if len(reference) < 20:
        return None
    import random

    rng = random.Random(seed)
    shuffled = reference[:]
    rng.shuffle(shuffled)
    mid = len(shuffled) // 2
    half_a, half_b = shuffled[:mid], shuffled[mid:]
    dist_a = _dist([normalize_v2(t) for t in half_a])
    dist_b = _dist([normalize_v2(t) for t in half_b])
    return jensen_shannon(dist_a, dist_b)


def run_realism() -> dict[str, float]:
    ref = load_reference()
    gen = load_generated_by_condition()
    if not ref or not gen:
        return {}  # harness renders this as "no_candidate"
    ref_dist = _dist([normalize_v2(t) for t in ref])
    return {
        cond: jensen_shannon(_dist([normalize_v2(t) for t in texts]), ref_dist)
        for cond, texts in gen.items()
    }
