"""
Local reimplementation of the University of Moratuwa (UoM) Sinhala Romaniser
ruleset: https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php

Per the "no live calls in a loop" rule that governs this repo, the live
endpoint was called exactly ONCE, to build a 20-item calibration sample
(scripts/verify_uom_endpoint.py ->
data/gold/uom_endpoint_verification.jsonl). No public source or documented
ruleset exists for that tool (its footer cites an unrelated paper that
doesn't describe the algorithm; no linked repo, no GitHub user found for the
author), so this table was derived by hand from that 20-item sample plus
standard Sinhala grapheme-to-Latin phonetics, then checked against the
sample with `python scripts/verify_uom_endpoint.py --diff` (local only, no
further network calls).

Two DELIBERATE, DOCUMENTED deviations from the live tool's literal output,
kept because matching them would only hurt this backend's actual purpose
(scoring well against real human-typed Swa-Bhasha Singlish) with no
compensating benefit:
  1. No capitalization. The live tool capitalizes the first letter of most
     (not all — e.g. "ටීවී එක..." comes back lowercase) outputs; this looks
     like an incidental quirk/bug rather than a rule, and real Singlish
     texting isn't reliably capitalized either. This reimplementation always
     lowercases.
  2. ZWJ is stripped, not passed through. The live tool leaves the U+200D
     zero-width joiner literally embedded in conjunct output (e.g.
     'buddhap‍rathimaavee') — an invisible character with no Latin-script
     analog. Swa-Bhasha's real reference text never contains one, so keeping
     it would only ever add edit-distance cost.

Everything else (per-consonant/vowel-sign mapping, virama dropping the
inherent vowel, non-Sinhala passthrough) matches the calibration sample.
Operates on grapheme clusters (src.graphemes.clusters) — Sinhala syllables
are multi-codepoint, so a vowel sign or virama is never processed apart
from its base consonant.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import clusters, ZWJ, ZWNJ  # noqa: E402

VIRAMA = "්"

# Independent vowels (standalone, own grapheme cluster).
_INDEPENDENT_VOWELS = {
    "අ": "a", "ආ": "aa", "ඇ": "ae", "ඈ": "aee",
    "ඉ": "i", "ඊ": "ii", "උ": "u", "ඌ": "uu",
    "ඍ": "ru", "ඎ": "ruu", "ඏ": "lu", "ඐ": "luu",
    "එ": "e", "ඒ": "ee", "ඓ": "ai",
    "ඔ": "o", "ඕ": "oo", "ඖ": "au",
}

# Dependent vowel signs — replace the consonant's inherent 'a'.
_VOWEL_SIGNS = {
    "ා": "aa", "ැ": "ae", "ෑ": "aee",
    "ි": "i", "ී": "ii", "ු": "u", "ූ": "uu",
    "ෘ": "ru", "ෲ": "ruu", "ෟ": "lu",
    "ෙ": "e", "ේ": "ee", "ෛ": "ai",
    "ො": "o", "ෝ": "oo", "ෞ": "au",
}

# Consonants, as rendered WITH their inherent 'a' (used when no vowel sign
# or virama follows in the same cluster).
_CONSONANTS = {
    "ක": "ka", "ඛ": "kha", "ග": "ga", "ඝ": "gha", "ඞ": "nga", "ඟ": "nga",
    "ච": "cha", "ඡ": "cha",  # ඡ calibrated to "cha" not "chha" — confirmed
                             # against the live sample ("ඡනනාටක" -> "chananaataka")
    "ජ": "ja", "ඣ": "jha", "ඤ": "nya", "ඥ": "gna",
    "ට": "ta", "ඨ": "tha", "ඩ": "da", "ඪ": "dha", "ණ": "na", "ඬ": "nda",
    "ත": "tha", "ථ": "thha", "ද": "da", "ධ": "dha", "න": "na", "ඳ": "nda",
    "ප": "pa", "ඵ": "pha", "බ": "ba", "භ": "bha", "ම": "ma", "ඹ": "mba",
    "ය": "ya", "ර": "ra", "ල": "la", "ව": "va",
    "ශ": "sha", "ෂ": "sha", "ස": "sa", "හ": "ha", "ළ": "la", "ෆ": "fa",
}

# Standalone combining signs (their own grapheme cluster when not attached
# to a preceding consonant — practically, still map the same way when found
# trailing a consonant cluster since src.graphemes groups them together).
_ANUSVARA = "ං"  # nasalization -> n
_VISARGA = "ඃ"   # aspiration -> h


def _convert_cluster(cluster: str) -> str:
    if cluster.isascii():
        return cluster
    if cluster in _INDEPENDENT_VOWELS:
        return _INDEPENDENT_VOWELS[cluster]

    # A cluster is base-consonant (+ optional vowel sign / virama / anusvara
    # / visarga / ZWJ). Walk it left to right.
    out = ""
    i = 0
    n = len(cluster)
    while i < n:
        ch = cluster[i]
        if ch in _CONSONANTS:
            base = _CONSONANTS[ch]
            nxt = cluster[i + 1] if i + 1 < n else ""
            if nxt == VIRAMA:
                out += base[:-1]  # drop inherent 'a'
                i += 2
            elif nxt in _VOWEL_SIGNS:
                out += base[:-1] + _VOWEL_SIGNS[nxt]
                i += 2
            else:
                out += base
                i += 1
        elif ch == _ANUSVARA:
            out += "n"
            i += 1
        elif ch == _VISARGA:
            out += "h"
            i += 1
        elif ch in _VOWEL_SIGNS:
            # Vowel sign with no preceding consonant in this cluster
            # (shouldn't normally happen — defensive fallback).
            out += _VOWEL_SIGNS[ch]
            i += 1
        elif ch in (ZWJ, ZWNJ):
            # Deliberately stripped — see module docstring, deviation #2.
            i += 1
        else:
            i += 1  # unmapped codepoint: skip rather than crash
    return out


def romanize(sinhala_text: str) -> str:
    """Sinhala -> romanized Singlish, UoM-style ruleset (see module docstring
    for the two documented deviations from the live tool's literal output)."""
    return "".join(_convert_cluster(c) for c in clusters(sinhala_text))
