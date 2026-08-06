"""
Misspelling noise vector: grapheme-cluster-level perturbations (drop, swap,
substitute) that mimic realistic typos.

STUB — Phase 3. Not yet implemented (Phase 0 is verifier-only).
Must operate on grapheme clusters (src/graphemes.py), never raw codepoints,
since Sinhala syllables are multi-codepoint.

Interface (set in Phase 2, src/noisers/transliteration.py): returns
(noisy_text, realised_noise_rate) so callers can populate schema.Row's
realised_noise_rate truthfully instead of guessing at it.
"""

from __future__ import annotations


def apply(text: str, severity: str, seed: int) -> tuple[str, float]:
    """Sinhala -> misspelled text at the given severity ("light" | "heavy").
    Returns (noisy_text, realised_noise_rate)."""
    raise NotImplementedError("TODO(Phase 3): misspelling noiser")
