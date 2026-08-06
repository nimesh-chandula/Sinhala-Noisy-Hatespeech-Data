"""
Romanizer backend: wraps the `aksharamukha` PyPI library
(https://pypi.org/project/aksharamukha/, virtualvinodh/aksharamukha).

Aksharamukha has genuine Sinhala support and exposes two Latin-script
schemes worth comparing in the bake-off:
  - 'RomanColloquial': plain-ASCII, casual-spelling output — closest to how
    people actually type Singlish, and the expected stronger candidate.
  - 'SinhalaRomanLoC': formal Library-of-Congress-style transliteration with
    diacritics (ā, ś, ṭ, ...) — kept as a comparison point, expected weaker
    for this project's purpose (nobody types diacritics casually) but useful
    to confirm that expectation empirically rather than assume it.

Verified by reading aksharamukha/transliterate.py directly that the
library makes exactly one network call in its entire codebase,
gated on `src == "Tamil" and tgt == "IPA"` — never triggered by the Sinhala
calls here, so it's safe to run inside the eval harness loop.

--- v -> w correction (Phase 1 bake-off finding) ---
'RomanColloquial' renders ව as "v" (e.g. ලංකාව -> "lankava"), but real
Singlish and the Swa-Bhasha gold set both consistently write it "w"
(-> "lankawa"). This is a systematic orthographic-convention difference for
one specific phoneme, not a per-example fit — applying it dropped this
backend's gold_cer word_multi_min from 0.111 to 0.067 (measured against the
full 2000-word/400-sentence gold set, not a handful of cherry-picked
examples), clearing the Phase 1 target of < 0.10.

--- ත/ට disambiguation correction (Phase 2 realism-diagnosis finding) ---
'RomanColloquial' collapses ත (dental "tha") and ට (retroflex "ta") to the
same plain "t" (e.g. කතා -> "kata"; real Singlish/Swa-Bhasha write "katha").
This is a genuine accuracy fix, not realism-only: it also improved gold_cer
(word_multi_min 0.067 -> 0.042, sent_single 0.128 -> 0.111 on the full gold
set), so no metric was traded for another.

The naive fix — post-process the OUTPUT string — doesn't work: ත and ට
produce identical "t..." output, so there's nothing in the string to key
off. The next-naive fix — process the SOURCE text grapheme-cluster by
grapheme-cluster and patch clusters based on their Sinhala base character —
also doesn't work: verified directly that aksharamukha's anusvara handling
is context-dependent on what FOLLOWS a cluster (ලං alone -> "lam", but
ලංකා -> "lanka" — the same substring rendered differently once the next
consonant is known), so isolated per-cluster calls silently corrupt
anusvara-adjacent words if used naively.

The fix that actually works: substitute ත -> ථ (aspirated dental "thha") in
the SOURCE text before calling aksharamukha, once, on the whole text/word —
never split into clusters, so all cross-cluster context (anusvara
assimilation etc.) is computed correctly exactly as aksharamukha intends.
Verified ථ already renders with a leading "th" in every vowel/virama
combination (ථ->tha, ථි->thi, ථු->thu, ථ්->th — always exactly one
character longer than ත's plain "t"-form), so the substitution is a plain
1:1 base-codepoint swap: it never touches or reorders any attached vowel
sign, virama, or ZWJ, so it stays grapheme-safe (operating on grapheme
clusters, never raw characters, since Sinhala syllables are multi-codepoint)
without needing to split into clusters at all.

--- Loanword override table (manual-review finding) ---
SOLD's original text often contains English loanwords already spelled out
phonetically in Sinhala script (e.g. ලව් = Sinhala spelling of "love").
Phonetically transliterating these back produces nonsense that doesn't
match either the original English word or real Singlish spelling (love ->
"law", අකවුන්ට් -> "akawunt" instead of "account"). Caught during a manual
review of a 100-item sample; scale confirmed by scanning the full SOLD
corpus (not just the review sample): word frequency in SOLD, cross-referenced against
Swa-Bhasha's attested romanizations and a common-English-word list,
surfaced 248 candidates — the large majority were coincidental collisions
with common native Sinhala words (`ගඟ`/"river" -> "gang", `පාරක්`/"once" ->
"park", `නම්`/"if" -> "name") that a naive automated filter could not
safely distinguish from genuine loanwords, so every entry below was
individually verified against its real Sinhala meaning before inclusion —
this table is NOT the output of an automated dictionary match.

Applied per-word (via `src.graphemes.text_runs`, already used elsewhere in
this codebase) rather than as a whole-text substitution, so a known
loanword's correct spelling completely bypasses the phonetic path (and the
v->w fix, which would otherwise wrongly turn "love" into "lowe"). Verified
safe: Phase 2 already established that per-WORD aksharamukha calls are
compositional with whole-text calls (only per-CLUSTER calls broke
cross-cluster context like anusvara assimilation), so segmenting at the
word level here doesn't reintroduce that bug.

`romanize_colloquial()` (all corrections applied) is what later phases
use; `romanize_colloquial_raw()` stays a single whole-text call to the
unmodified library, kept only so the Phase 1 bake-off record shows each
correction's effect transparently.

Per-word calls carry real per-call overhead (measured ~30ms/post
unmemoized, vs. ~1.4ms/post for the old single whole-text call) — but
SOLD's vocabulary is Zipfian (34,747 distinct words cover 10,000 posts), so
`_romanize_word` is memoized: measured 4.56ms/post steady-state over the
full corpus (139,148 cache hits vs. 34,747 misses).
"""

from __future__ import annotations

import functools
import sys
from pathlib import Path

from aksharamukha import transliterate

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402

_SRC = "Sinhala"
_THA = "ත"
_THHA = "ථ"  # ථ already renders "th..." — substituting ත -> ථ fixes the collapse

# Sinhala -> correct English spelling, for words that are phonetic Sinhala
# renderings of English loanwords rather than native Sinhala vocabulary.
# See module docstring for how this was built and verified.
_LOANWORD_OVERRIDES = {
    # From the initial 100-item review sample (24):
    "ලව්": "love", "ලික්": "leak", "අකවුන්ට්": "account", "බ්ලොක්": "block",
    "ලිනක්ස්": "linux", "අයිටී": "it", "ඩිපාට්මන්ට්": "department",
    "කොරෝනා": "corona", "චයීනීස්": "chinese", "ඩොලර්": "dollar",
    "ඔෆිස්": "office", "පේජ්": "page", "හැන්සම්": "handsome",
    "රේසිං": "racing", "සයිකල්": "cycle", "බයිසිකල්": "bicycle",
    "ඩාලින්": "darling", "ඩිල්": "deal", "නිව්ස්": "news", "ටෝක්ස්": "talks",
    "ඉශූ": "issue", "මාකට්": "market", "ලයින්": "line", "ඇක්ශන්": "action",
    "රිප්ලයි": "reply",
    # From the full-corpus frequency scan, individually verified (65):
    "ක්‍රිකට්": "cricket", "ලයික්": "like", "පොලිස්": "police",
    "බෝම්බ": "bomb", "කමෙන්ට්": "comment", "ෆේල්": "fail", "නයිට්": "night",
    "ගුඩ්": "good", "බෝඩ්": "board", "ලයිට්": "light", "ටයිම්": "time",
    "කැබිනට්": "cabinet", "ලයිෆ්": "life", "ඩයලොග්": "dialog",
    "ජනවාරි": "january", "කාඩ්": "card", "මයික්": "mike", "ටවුන්": "town",
    "ක්ලාස්": "class", "බියර්": "beer", "පැකට්": "packet", "කෝට්": "coat",
    "මීටර්": "meter", "ටයිප්": "type", "තෑන්ක්ස්": "thanks",
    "ලෙවල්": "level", "ඇමරිකන්": "american", "පේපර්": "paper",
    "රූම්": "room", "ෆුල්": "full", "බීච්": "beach", "ප්ලෑන්": "plan",
    "ශෙයා": "share", "කොපි": "copy", "ෆ්‍රී": "free", "ඇපල්": "apple",
    "ප්ලාස්ටික්": "plastic", "ප්‍රොෆයිල්": "profile",
    "ඔන්ලයින්": "online", "චෙක්": "check", "ට්‍රැක්": "track",
    "වයිෆ්": "wife", "එක්සෑම්": "exam", "ෆයිල්": "file",
    "බර්ත්ඩේ": "birthday", "මේජර්": "major", "ඩිලීට්": "delete",
    "පෙබරවාරි": "february", "බ්‍රේක්": "break", "ඩුබායි": "dubai",
    "ස්ට්‍රයික්": "strike", "අප්‍රේල්": "april", "ඉන්ටර්නෙට්": "internet",
    "සුපර්": "super", "සීසන්": "season", "ඔරිජිනල්": "original",
    "කාපට්": "carpet", "ස්වීට්": "sweet", "වර්ල්ඩ්": "world",
    "ෆ්‍රෙන්ඩ්": "friend", "ජීප්": "jeep", "සිවිල්": "civil",
    "මේකප්": "makeup", "සුනාමි": "tsunami", "සීරීස්": "series",
    "රෙකෝඩ්": "record", "අප්ඩේට්": "update", "නම්බර්": "number",
    "ශුවර්": "sure", "ඕඩර්": "order", "රෙජිස්ටර්": "register",
    "මාර්තු": "march", "ජූලි": "july", "රොකට්": "rocket", "පාටි": "party",
    "ටියුබ්": "tube", "ක්‍රොස්": "cross", "ෆයිනල්": "final",
    "බර්ත්": "birth", "සපොර්ට්": "support", "කානිවල්": "carnival",
    "සෙකන්ඩ්": "second", "ෆෙඩරල්": "federal", "බේබි": "baby",
    "පෝස්ටර්": "poster", "මෝටර්": "motor", "පාස්වර්ඩ්": "password",
    "මේල්": "mail", "වයිෆයි": "wifi", "ප්‍රයිස්": "price",
    "දෙසැම්බර්": "december", "ජනරාල්": "general", "ඩොක්ටර්": "doctor",
    "ක්ලික්": "click", "බටර්": "butter", "ප්‍රෙස්": "press", "ඩවුන්": "down",
    "මාක්ස්": "marks",
}


def romanize_colloquial_raw(sinhala_text: str) -> str:
    """Sinhala -> Singlish via aksharamukha's 'RomanColloquial' scheme, unmodified."""
    return transliterate.process(_SRC, "RomanColloquial", sinhala_text)


def _romanize_word(word: str) -> str:
    """Corrected romanization of a single Sinhala word (loanword override,
    then ත/ට + v->w fixes)."""
    override = _LOANWORD_OVERRIDES.get(word)
    if override is not None:
        return override
    substituted = word.replace(_THA, _THHA)
    raw = transliterate.process(_SRC, "RomanColloquial", substituted)
    return raw.replace("v", "w").replace("V", "W")


_romanize_word = functools.lru_cache(maxsize=200_000)(_romanize_word)


def romanize_colloquial(sinhala_text: str) -> str:
    """Sinhala -> Singlish via 'RomanColloquial', with the loanword, v->w,
    and ත/ට corrections (see module docstring). This is the winning Phase 1
    backend. Processes per-word (via text_runs) so loanword overrides can
    bypass the phonetic path entirely."""
    return "".join(
        run if not is_sinhala else _romanize_word(run)
        for is_sinhala, run in text_runs(sinhala_text)
    )


def romanize_loc(sinhala_text: str) -> str:
    """Sinhala -> formal romanization via aksharamukha's 'SinhalaRomanLoC' scheme."""
    return transliterate.process(_SRC, "SinhalaRomanLoC", sinhala_text)
