"""
Abbreviation noise vector: shorten common words/phrases the way real users do
in casual Sinhala social-media text.

STUB — Phase 4. Not implemented in Phase 0 (verifier-only session).

Interface (set in Phase 2, src/noisers/transliteration.py): returns
(noisy_text, realised_noise_rate) so callers can populate schema.Row's
realised_noise_rate truthfully instead of guessing at it.
"""

from __future__ import annotations


def apply(text: str, severity: str, seed: int) -> tuple[str, float]:
    """Sinhala -> abbreviated text at the given severity ("light" | "heavy").
    Returns (noisy_text, realised_noise_rate)."""
    raise NotImplementedError("TODO(Phase 4): abbreviation noiser")
