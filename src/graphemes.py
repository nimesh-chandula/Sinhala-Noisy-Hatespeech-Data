"""
Grapheme-cluster utilities — the single place in this repo that knows how to
split Sinhala text without breaking a syllable.

This project operates on grapheme clusters, not raw codepoints, everywhere:
Sinhala syllables are multi-codepoint (base consonant + vowel sign +
optional ZWJ + optional consonant, e.g. "ක්‍ෂ" = 4 codepoints, one
cluster). Every noiser and every metric that indexes into text by "character"
must go through `clusters()` here instead of iterating `str` directly.

Primary implementation uses the `regex` module's Unicode extended grapheme
cluster support (`\\X`). A pure-`unicodedata`
fallback is provided in case `regex` is ever unavailable in an environment —
it is deliberately Sinhala-aware (handles combining marks, ZWJ, and virama)
rather than a generic approximation.
"""

from __future__ import annotations

import unicodedata

try:
    import regex as _regex
    _HAS_REGEX = True
except ImportError:  # pragma: no cover - exercised only if `regex` is missing
    _regex = None
    _HAS_REGEX = False

# Sinhala Unicode block, for reference / sanity checks elsewhere.
SINHALA_RANGE = range(0x0D80, 0x0E00)
ZWJ = "‍"
ZWNJ = "‌"

_GRAPHEME_PATTERN = _regex.compile(r"\X") if _HAS_REGEX else None


def clusters(text: str) -> list[str]:
    """Split `text` into extended grapheme clusters.

    This is the ONLY sanctioned way to index into Sinhala text in this repo.
    `list(text)` or `text[i]` split mid-syllable and must not be used on
    Sinhala content.
    """
    if not text:
        return []
    if _HAS_REGEX:
        return _GRAPHEME_PATTERN.findall(text)
    return _fallback_clusters(text)


def _fallback_clusters(text: str) -> list[str]:
    """Sinhala-aware clustering without the `regex` module.

    Groups each base codepoint with any following combining marks (Unicode
    category Mn/Mc — this covers Sinhala vowel signs and virama) and any
    ZWJ/ZWNJ-joined continuations (needed for conjuncts like ක්‍ෂ).
    Not a full Unicode UAX #29 implementation, but correct for the scripts
    this project handles (Sinhala + ASCII).
    """
    out: list[str] = []
    buf = ""
    for ch in text:
        cat = unicodedata.category(ch)
        is_combining = cat in ("Mn", "Mc") or ch in (ZWJ, ZWNJ)
        if is_combining and buf:
            buf += ch
        else:
            if buf:
                out.append(buf)
            buf = ch
    if buf:
        out.append(buf)
    return out


def is_lossless(text: str) -> bool:
    """True if re-joining `clusters(text)` reproduces `text` exactly.

    A cheap round-trip sanity check: clustering must never lose or reorder
    codepoints, only group them.
    """
    return "".join(clusters(text)) == text


def starts_with_combining(cluster: str) -> bool:
    """True if `cluster` begins with a combining mark or ZWJ/ZWNJ.

    A cluster should never legitimately start this way — used by
    grapheme-integrity checks to catch a mid-syllable split.
    """
    if not cluster:
        return False
    ch = cluster[0]
    return unicodedata.category(ch) in ("Mn", "Mc") or ch in (ZWJ, ZWNJ)


def contains_sinhala(text: str) -> bool:
    """True if any codepoint in `text` falls in the Sinhala Unicode block."""
    return any(ord(ch) in SINHALA_RANGE for ch in text)


def grapheme_len(text: str) -> int:
    """Length of `text` in grapheme clusters (not codepoints)."""
    return len(clusters(text))


def text_runs(text: str) -> list[tuple[bool, str]]:
    """Split `text` into (is_sinhala, run_text) segments on grapheme-cluster
    boundaries, so a run never splits a conjunct or vowel-sign attachment.

    Each contiguous span of Sinhala clusters becomes one run; everything
    else (spaces, digits, punctuation, Latin letters) becomes another. In
    practice, since words are whitespace-separated, a Sinhala run is a
    single Sinhala word. Shared by src/romanizers/indic.py (segmenting
    around the vendored singlish package's space-dropping bug) and
    src/noisers/transliteration.py (per-word spelling-variance injection).
    """
    segments: list[tuple[bool, str]] = []
    current_flag: bool | None = None
    current_chars: list[str] = []
    for cluster in clusters(text):
        flag = contains_sinhala(cluster)
        if flag != current_flag:
            if current_chars:
                segments.append((current_flag, "".join(current_chars)))
            current_flag = flag
            current_chars = [cluster]
        else:
            current_chars.append(cluster)
    if current_chars:
        segments.append((current_flag, "".join(current_chars)))
    return segments
