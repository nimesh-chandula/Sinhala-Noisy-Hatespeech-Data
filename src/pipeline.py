"""
Compound noising pipeline: applies noise vectors in a fixed order to produce
the "compound" condition (Phase 4) and drives full generation (Phase 5).

STUB — Phase 3/4. Not implemented in Phase 0 (verifier-only session).

Fixed order (do not reorder between runs — determinism depends on it):
    transliteration -> codemix -> misspell -> abbreviate
"""

from __future__ import annotations

NOISER_ORDER = ("transliteration", "codemix", "misspell", "abbreviate")


def run(text: str, severity: str, seed: int, conditions: tuple[str, ...] = NOISER_ORDER):
    """Apply the requested noisers in NOISER_ORDER, seeded for determinism."""
    raise NotImplementedError("TODO(Phase 3/4): compound pipeline")
