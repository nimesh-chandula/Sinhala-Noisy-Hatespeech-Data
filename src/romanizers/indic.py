"""
Romanizer backend: wraps the vendored `singlish` package (asanka9/singlish,
MIT) — see src/romanizers/_vendor/singlish_sinhala_to_singlish.py for the
unmodified original and full attribution.

REPURPOSED FROM `indic-transliteration`: the original plan named
`indic-transliteration` as this slot's candidate, but its source was
inspected directly (full repo tree fetched and searched) and it has ZERO
Sinhala support — no file anywhere in the package mentions "sinhala", and
its supported Brahmic script classes are only Devanagari, Bengali, Telugu,
Kannada, Gurmukhi, and Tamil. It cannot be wrapped for this bake-off at
all. `singlish` was substituted instead: a small, genuinely
Sinhala->Singlish PyPI package.

Why a wrapper is needed (not just calling the vendored class directly):
`SinhalaToSinglish.convert()` iterates per Unicode codepoint over the WHOLE
input, and any character not in its lookup table — spaces, digits,
punctuation, English letters — falls into a bare `except:` that silently
drops it. Fed a full sentence, this concatenates every word together with
no spaces. This wrapper segments the input into Sinhala/non-Sinhala runs
first (on grapheme-cluster boundaries — Sinhala syllables are
multi-codepoint, so a run boundary must never fall mid-conjunct), converts
only the Sinhala runs, and
splices non-Sinhala runs back in unchanged. The vendored mapping table
itself is untouched — this keeps the bake-off comparing the original
third-party rule table, not our patch of it.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402
from src.romanizers._vendor.singlish_sinhala_to_singlish import SinhalaToSinglish  # noqa: E402


def romanize(sinhala_text: str) -> str:
    """Sinhala -> Singlish via the vendored asanka9/singlish table, with
    spaces/punctuation/digits preserved (the fix this wrapper exists for)."""
    converter = SinhalaToSinglish()
    out_parts: list[str] = []
    for is_sinhala, run in text_runs(sinhala_text):
        out_parts.append(converter.convert(run) if is_sinhala else run)
    return "".join(out_parts)
