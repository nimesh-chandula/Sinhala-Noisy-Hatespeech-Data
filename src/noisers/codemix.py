"""
Code-mixing noise vector: interleave English/Singlish tokens into Sinhala text.

STUB — Phase 3. Not implemented in Phase 0 (verifier-only session).

Interface (set in Phase 2, src/noisers/transliteration.py): returns
(noisy_text, realised_noise_rate) so callers can populate schema.Row's
realised_noise_rate truthfully instead of guessing at it.
"""

from __future__ import annotations


def apply(text: str, severity: str, seed: int) -> tuple[str, float]:
    """Sinhala -> code-mixed text at the given severity ("light" | "heavy").
    Returns (noisy_text, realised_noise_rate)."""
    raise NotImplementedError("TODO(Phase 3): code-mix noiser")
