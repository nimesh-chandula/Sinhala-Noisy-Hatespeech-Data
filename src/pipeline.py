"""
Compound noising pipeline: applies noise vectors in a fixed order to produce
the "compound" condition (Phase 4) and drives full generation (Phase 5).

STUB — Phase 3/4. Not implemented in Phase 0 (verifier-only session).

Fixed order (do not reorder between runs — determinism depends on it):
    codemix -> transliteration -> misspell -> abbreviate

Codemix runs BEFORE transliteration, not after (revised from the original
transliteration -> codemix ordering once codemix was actually designed in
Phase 3). Code-mixing is a WORD-CHOICE decision (which language a word is
written in, matched against Sinhala-script surface forms in
data/lexicon/codemix_lexicon.jsonl) made before a typist picks a
script/spelling for whatever Sinhala remains — not a script/spelling
decision itself. Concretely: transliteration converts all remaining
Sinhala to Latin script, so if it ran first, codemix's Sinhala-keyed
lexicon would have no Sinhala left to match against downstream. Running
codemix first means it always sees the same Sinhala input its lexicon was
built from, and transliteration then romanizes only whatever codemix left
in Sinhala script — matching how a real bilingual typist actually composes
a sentence (choose the words, then spell them).
"""

from __future__ import annotations

NOISER_ORDER = ("codemix", "transliteration", "misspell", "abbreviate")


def run(text: str, severity: str, seed: int, conditions: tuple[str, ...] = NOISER_ORDER):
    """Apply the requested noisers in NOISER_ORDER, seeded for determinism."""
    raise NotImplementedError("TODO(Phase 3/4): compound pipeline")
