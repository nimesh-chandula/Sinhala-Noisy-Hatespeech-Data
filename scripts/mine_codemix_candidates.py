"""
Phase 3 density expansion, step 1 — mine a WIDE candidate table for manual
review, per the user's explicit request after reviewing real codemix output
and finding 85.8%/79.7% of light/heavy rows unchanged. Root cause measured
precisely (see LOG.md "Phase 3 density expansion"): only 21.85% of SOLD
posts contain ANY word in the 210-entry lexicon — that's a coverage
ceiling, not a severity-tuning problem, and closing it requires reviewing
far more candidate words than the original phase did.

This script does NOT decide anything — unlike build_codemix_lexicon.py's
original hand-verification (done by the agent alone), this batch is wide
enough that final accept/reject calls belong to a native speaker. It
produces a CSV with a best-guess `proposed_english` per row and empty
`accept`/`final_english` columns for the user to fill in.

--- Candidate selection ---
1. Every distinct Sinhala surface form across SOLD train+test
   (src.graphemes.text_runs, same tokenization as build_codemix_lexicon.py),
   excluding the 2,000-word CER heldout set and the 210 forms already
   resolved in data/lexicon/codemix_lexicon.jsonl.
2. A stoplist (_STOPLIST below) of confirmed pronouns/demonstratives/
   particles/negators/copulas — closed-class function words are high-
   frequency but low-type-count, so a few hundred entries covers the
   overwhelming majority of non-content words in the top frequency ranks.
3. A light suffix heuristic (_VERB_SUFFIXES) flags PROBABLE verb
   inflections with a note rather than excluding them outright — verb
   morphology is open-class (any verb has ~10 inflected surface forms), so
   a stoplist can't cover it, and this noiser stays out of verb-translation
   scope regardless (see data/lexicon/codemix_rejected_candidates.md:
   "හිතන — verb form, out of scope"). Flagged, not removed, so nothing is
   hidden from review.
4. Every one of the ~28 previously-rejected candidates from
   data/lexicon/codemix_rejected_candidates.md that was rejected for a
   RISK/AMBIGUITY/ATTESTATION judgment call (not a flat mistranslation —
   see _PREVIOUSLY_REJECTED below for which ones and why) is included,
   carrying its original reason, for the user to re-adjudicate with full
   context. Words rejected because the proposed English was simply WRONG
   (e.g. "සඳ"="moon" mismatched to "scandal" by the old automated scan) are
   NOT re-included under their old wrong pairing — they flow through the
   normal frequency-mining path instead, so if they surface again it's with
   a fresh, correct proposed translation.
5. Cut off at SOLD frequency >= 2 (singletons contribute negligibly and
   number in the tens of thousands — see the coverage-curve investigation
   in LOG.md), capped at the top ~12,000 surviving candidates.

Run:  python scripts/mine_codemix_candidates.py
Writes data/lexicon/codemix_candidates_review.csv:
  rank, sinhala, sold_frequency, prior_status, proposed_english,
  confidence_note, accept, final_english
(accept, final_english are left blank for manual review)
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
SOLD_DIR = DATA_DIR / "sold"
HELDOUT_PATH = DATA_DIR / "gold" / "heldout_words.txt"
LEXICON_PATH = DATA_DIR / "lexicon" / "codemix_lexicon.jsonl"
LEXICON_DIR = DATA_DIR / "lexicon"
OUTPUT_PATH = LEXICON_DIR / "codemix_candidates_review.csv"

MIN_FREQUENCY = 2
MAX_CANDIDATES = 12000

# --- Closed-class function words: pronouns, demonstratives, particles,
# negators, common existential/copula forms. Deliberately over-inclusive
# within this category (a missed function word just wastes one review row;
# it's never presented as a false "content word"). Compiled from the
# top-400 SOLD frequency dump gathered during the original Phase 3
# investigation, plus general Sinhala closed-class vocabulary. ---
_STOPLIST = {
    # 1st/2nd/3rd person pronouns, all case-marked forms observed
    "මම", "මට", "මං", "මන්", "මගේ", "මගෙ", "මාව", "මාත්", "මාගේ", "මාත්",
    "අපි", "අපේ", "අපිට", "අපිත්", "අප", "අපට", "අපටත්", "අපිටත්", "අප්පා",
    "ඔයා", "ඔය", "ඔයාට", "ඔයාගෙ", "ඔයාගේ", "ඔයාලට", "ඔයාලටත්", "ඔයාලා",
    "ඔබ", "ඔබට", "ඔබේ", "ඔබට", "ඔබෙන්",
    "එයා", "එයාට", "එයාගේ", "එයාගෙ", "එවුන්", "එවුන්ට",
    "උන්", "උන්ට", "උන්ගේ", "උන්ගෙ", "උනි",
    "ඌ", "ඌට", "ඌගේ", "ඌව",
    "මූ", "මූට", "මුන්", "මුන්ට",
    "තෝ", "තොපි", "තොට", "තොපිට", "තොපේ", "තොගෙ", "තොගේ",
    "උඹ", "උඹට", "උඹේ", "උඹලා", "උඹෙ", "උඹෙන්",
    "තමා", "තමන්", "තමන්ගේ", "තමන්ගෙ", "තමුසෙ", "තමයි",
    "ඈ", "ඕහු", "ඔහු", "ඇය", "ඔවුන්", "ඔවුන්ට", "ඔවුන්ගේ",
    # demonstratives / determiners
    "මේ", "ඒ", "මෙය", "ඒක", "ඕක", "මේක", "මේකේ", "මේකට", "මේකෙ",
    "ඒවා", "මේවා", "ඕවා", "මේව", "ඒවට", "මේවට",
    "මෙම", "එම", "මෙහෙම", "එහෙම", "මෙන්න", "අන්න", "ඔන්න",
    "මෙතන", "එතන", "මෙහෙ", "එහේ", "මෙතනින්", "එතනින්",
    "එකා", "එකාට", "එක්කෙනා", "අය", "අයට",
    # particles / conjunctions / discourse markers
    "කියලා", "කියල", "කියන්නේ", "කියන්නෙ", "කියලද", "කියලත්", "කිය", "කියා",
    "වගේ", "වගෙ", "වගේම", "නම්", "නම", "ද", "ට", "ක්", "ම", "ලු", "වත්",
    "ත්", "නේ", "නේද", "එහෙනම්", "එහෙනම", "ඉතින්", "ඉතිං", "නිසා", "හින්දා",
    "නමුත්", "ඒත්", "එතකොට", "එත", "තව", "තවත්", "විතරයි", "විතරක්",
    "විතර", "පමණයි", "පමණක්", "යි", "වෙනුවෙන්", "වෙනුවට", "අනුව", "විසින්",
    "සමග", "එක්ක", "එක්කො", "එක්කොත්", "සමඟ", "ගැන", "ගැනත්", "වෙත", "දක්වා",
    "පිළිබඳ", "වශයෙන්", "වශයෙනුත්", "යනු", "යැයි", "යයි",
    # negators
    "නෑ", "නැ", "නැහැ", "නැති", "නැත", "නැත්තම්", "නැත්තන්", "නැතුව",
    "නැතිව", "බෑ", "බැහැ", "එපා", "එපැයි", "නොවේ", "නොවෙයි", "නෙවෙයි",
    "නෙමෙයි", "නෙමේ", "නොදී", "නොකර",
    # existential / copula / common light verbs & their frequent inflections
    "තියෙන", "තියෙනවා", "තියෙන්නේ", "තියෙන්නෙ", "තියෙන්න", "තියන", "තියනවා",
    "ඉන්න", "ඉන්නවා", "ඉන්නේ", "ඉන්නෙ", "ඉන්නව",
    "වෙනවා", "වෙන්න", "වෙන්නේ", "වෙන්නෙ", "වෙච්ච", "වෙන",
    "උනා", "උනාට", "උනත්", "උනේ", "උනාම", "වුනා", "වුනාට", "වුනාම",
    "ඇති", "ඇත", "ඕන", "ඕනේ", "ඕනෙ", "ඕනි", "ඕනෙම",
    "පුලුවන්", "පුළුවන්", "බැරි", "විය", "වූ", "වන",
    "කර", "කරන", "කරන්න", "කරනවා", "කරන්නේ", "කරන්නෙ", "කරලා", "කරල",
    "කරපු", "කරගෙන", "කරගන්න", "කරගත්තා",
    "දාන", "දාන්න", "දාන්නෙ", "දාන්නේ", "දාලා", "දාල", "දාපු",
    "ගන්න", "ගන්නේ", "ගන්නෙ", "ගත්තා", "ගත්තේ",
    "දෙන්න", "දෙනවා", "දෙන", "දුන්නා", "දුන්නේ", "දුන්නෙ",
    "යන්න", "යන", "යනවා", "යන්නේ", "යන්නෙ", "ගිය", "ගියා", "ගියේ",
    "බලන්න", "බලන", "බලා", "බලාගෙන", "බලපු",
    "කියන", "කියනවා", "කිව්වා", "කිව්වේ", "කිව්වෙ", "කියන්නට",
    "දකින", "දැක්කා", "දැක්කේ", "දැක්කම",
    "හිතන", "හිතන්න", "හිතාගෙන", "හිතුවා", "හිතුවේ", "හිතේ",
    # misc high-frequency short particles/interjections not content words
    "අනේ", "යකෝ", "බං", "බන්", "අඩෝ", "ඒකි", "ඒකිට", "ඕකි", "ඌව",
    "දැන්", "දැං", "අද", "ඊයේ", "හෙට", "දවසක්", "දවසට", "කවදාවත්",
    "සමහර", "හැම", "හැමෝ", "හැමෝම", "හැමදාම", "ඔක්කොම", "සියලුම",
    "එකම", "එකට", "එකේ", "එකෙන්", "එකක්", "එකයි", "එකත්", "එක", "එකෙක්",
    "එකකට", "එකකින්", "එකකට", "වලට", "වලින්", "වලදී", "වලත්", "වලින්ම",
    "ගානක්", "ගානට", "ගානේ",
}

# --- Verb-inflection suffix heuristic — imprecise by design, only used to
# ADD a "likely verb" note (never to exclude), since Sinhala verb
# morphology is open-class (any of thousands of verbs has ~10 inflected
# surface forms) and this noiser stays out of verb-translation scope
# regardless (see module docstring). ---
_VERB_SUFFIXES = ("න්න", "නවා", "න්නේ", "න්නෙ", "ගෙන", "පු", "ලා", "ල", "ුවා", "ුවේ")

# --- Previously-rejected candidates worth re-adjudicating: the proposed
# English was plausible/defensible, but excluded for a risk/ambiguity/
# attestation judgment call, not because it was a flat mistranslation.
# (sinhala_form, proposed_english, original_reason) ---
_PREVIOUSLY_REJECTED: list[tuple[str, str, str]] = [
    ("වැඩ", "work", "Too idiomatically overloaded — most real uses are slang for 'the situation/matter', not literally 'work'."),
    ("වැඩක්", "work එකක්", "Same as වැඩ — idiomatic overload risk."),
    ("වැඩේ", "work එක", "Same as වැඩ — idiomatic overload risk."),
    ("කතා", "talk", "Meaning too broad/context-dependent for a safe single-target substitution."),
    ("කතාව", "story", "Meaning too broad/context-dependent for a safe single-target substitution."),
    ("ගෑණි", "wife", "Frequently used pejoratively in this hate-speech corpus to mean 'woman' generically, not specifically 'wife' — risk of mistranslating the actual sense."),
    ("ගෙදර", "home", "'home' has zero attestation in the measured candidate vocabulary despite being independently plausible."),
    ("රට", "country", "'country' has zero attestation in the measured candidate vocabulary."),
    ("රටේ", "country එකේ", "Same as රට — zero attestation."),
    ("රටට", "country එකට", "Same as රට — zero attestation."),
    ("රටක්", "country එකක්", "Same as රට — zero attestation."),
    ("ලංකාව", "Lanka", "Proper noun — not a typical translation target."),
    ("ලංකාවේ", "Lanka එකේ", "Same as ලංකාව — proper noun."),
    ("ලංකාවෙ", "Lanka එකෙ", "Same as ලංකාව — proper noun."),
    ("ප්‍රශ්නය", "problem", "'problem' has zero attestation in the measured candidate vocabulary despite being independently plausible."),
    ("ප්‍රශ්නයක්", "problem එකක්", "Same as ප්‍රශ්නය — zero attestation."),
    ("පක්ෂය", "party", "Ambiguous with 'party' (celebration) sense, which IS already a verified loanword (පාටි->party) — risk of being misread as celebration in political posts."),
    ("ගින්න", "fire", "Common Sinhala slang for 'angry/heated', not literally 'fire', in many real uses — polysemy risk."),
    ("දෙයක්", "thing", "Too abstract/pronoun-like."),
    ("දේ", "thing", "Too abstract/pronoun-like."),
    ("දේවල්", "things", "Too abstract/pronoun-like."),
    ("මිනිස්සු", "people", "Redundant with ජනතාව->people (already included) — NOT a risk rejection, just was deemed stylistically redundant; safe to add now for density."),
    ("මිනිස්සුන්ට", "people ට", "Same as මිනිස්සු — redundancy, not risk."),
    ("කණ්ඩායම", "team", "SOLD frequency only 2 — negligible coverage value; ටීම් (loanword) already covers this concept."),
    ("චිත්‍රපටය", "film", "Zero attestation in SOLD at this inflection — casual Singlish doesn't typically use this formal word, but the translation itself is not wrong."),
    ("දුරකථනය", "phone", "Zero attestation — casual speech has no separate native word for this (posters already just write 'phone'); translation itself is not wrong."),
    ("උසාවිය", "court", "SOLD frequency only 1 — too rare to be worth the entry on its own, but translation is correct."),
    ("විරෝධතාව", "protest", "Zero occurrences of this exact form in SOLD — no coverage value regardless of decision."),
    ("ජනතාවගේ", "people's", "Grammatically awkward as a possessive English substitution."),
    ("මුස්ලිම්", "muslim", "ETHICAL FLAG, not an accuracy one: genuine common loanword (SOLD freq 59), but this is a religious/ethnic identity term in a HATE-SPEECH-labeled corpus — substituting identity markers inside potentially hateful sentences is a different, higher-risk kind of change than a neutral institutional/tech noun."),
]


def log(msg: str) -> None:
    print(f"[mine_codemix_candidates] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sold_word_frequency() -> dict[str, int]:
    freq: dict[str, int] = {}
    for split in ("train", "test"):
        with (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                for is_sinhala, run in text_runs(row["text"]):
                    if is_sinhala:
                        freq[run] = freq.get(run, 0) + 1
    return freq


def looks_like_verb(word: str) -> bool:
    return any(word.endswith(suf) for suf in _VERB_SUFFIXES)


def main() -> None:
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)

    freq = sold_word_frequency()
    heldout = {line.strip() for line in HELDOUT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()}
    lexicon_entries = _load_jsonl(LEXICON_PATH) if LEXICON_PATH.exists() else []
    already_resolved = {e["sinhala"] for e in lexicon_entries}
    log(f"SOLD vocabulary: {len(freq)} distinct forms; {len(heldout)} heldout; "
        f"{len(already_resolved)} already in the lexicon")

    rejected_map = {sinhala: (english, reason) for sinhala, english, reason in _PREVIOUSLY_REJECTED}

    rows: list[dict] = []

    # previously-rejected candidates first, regardless of stoplist/frequency
    # floor — the user asked to see all of them
    for sinhala, (english, reason) in rejected_map.items():
        rows.append({
            "sinhala": sinhala,
            "sold_frequency": freq.get(sinhala, 0),
            "prior_status": f"previously_rejected: {reason}",
            "proposed_english": english,
            "confidence_note": "",
        })

    # fresh frequency-mined candidates
    n_stopped = 0
    n_verb_flagged = 0
    for word, count in freq.items():
        if count < MIN_FREQUENCY:
            continue
        if word in heldout or word in already_resolved or word in rejected_map:
            continue
        if word in _STOPLIST:
            n_stopped += 1
            continue
        note = ""
        if looks_like_verb(word):
            note = "likely verb inflection — probably skip (out of scope)"
            n_verb_flagged += 1
        rows.append({
            "sinhala": word,
            "sold_frequency": count,
            "prior_status": "new",
            "proposed_english": "",
            "confidence_note": note,
        })

    rows.sort(key=lambda r: -r["sold_frequency"])
    rows = rows[:MAX_CANDIDATES]
    for i, row in enumerate(rows, 1):
        row["rank"] = i
        row["accept"] = ""
        row["final_english"] = ""

    log(f"{n_stopped} forms excluded via stoplist; {n_verb_flagged} flagged as likely-verb (kept, not excluded)")
    log(f"writing {len(rows)} candidate rows "
        f"({len(rejected_map)} previously-rejected + {len(rows) - len(rejected_map)} new)")

    with OUTPUT_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "sinhala", "sold_frequency", "prior_status",
            "proposed_english", "confidence_note", "accept", "final_english",
        ])
        writer.writeheader()
        writer.writerows(rows)
    log(f"wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
