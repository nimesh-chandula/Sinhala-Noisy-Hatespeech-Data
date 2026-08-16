"""
Phase 3 density expansion, step 2a — bulk-classify the 12,000-row candidate
table before manual translation, so per-word human/agent judgment is spent
only on words that actually need it.

A direct audit of the top 50 highest-frequency "new" candidates (see
LOG.md) found a 6% real yield rate: the rest split into a few recurring,
mechanically-detectable categories — closed-class function words the
original stoplist missed, slang intensifiers/adjectives with no clean
single-English-word target, and (SOLD being a hate-speech corpus) a
recurring set of slurs/vulgar insults that should never be assigned an
English gloss regardless of frequency. Auto-tagging these categories in
bulk is MORE consistent than 12,000 independent ad hoc judgment calls, not
less rigorous — the same word gets the same tag every time it recurs.

Every auto-tagged row keeps its Sinhala text and frequency in the CSV
(nothing is hidden) with a short category code in `confidence_note` and an
empty `proposed_english` — the user can always override any of them in
`final_english` during review. Only rows that survive ALL filters get
`confidence_note = "needs_manual_review"`, which is the pool
scripts/translate_codemix_candidates.py (next step) actually works through
by hand.

Run:  python scripts/classify_codemix_candidates.py
Rewrites data/lexicon/codemix_candidates_review.csv in place.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

CSV_PATH = REPO_ROOT / "data" / "lexicon" / "codemix_candidates_review.csv"

# --- Additional closed-class function words the original mining-script
# stoplist missed (found via direct audit of the top-50 highest-frequency
# candidates and subsequent batches). ---
_EXTRA_FUNC = {
    "ඇයි", "ටික", "ටිකක්", "ඔව්", "හා", "සහ", "මොකද", "හැබැයි", "කලින්",
    "පස්සෙ", "පස්ස", "පස්සේ", "කෙනෙක්", "මොන", "මොනවා", "මොනා", "මොකක්",
    "මොකක්ද", "මොකද්ද", "මොකටද", "කොහොමද", "කොහෙද", "කොච්චර", "කව්ද",
    "කවුද", "කවුරු", "කවුරුත්", "විට", "පසු", "අන්තිමට", "මුලින්ම",
    "වතාවක්", "පාරක්", "ගානක්", "වේවා", "යුතුයි", "යුතුය", "යුතු",
    "නිකන්", "ඔහොම", "අහවල්", "ඕන්නෑ", "ඕනෙම", "සියල්ල", "සියලු",
    "ඒවගේ", "මේවගේ", "අන්න", "ඔන්න", "දැක්කම", "කිව්වම", "ආවම", "ගියම",
    "වුනාම", "උනොත්", "කලොත්", "කිව්වොත්", "ආවොත්", "ගියොත්", "දුන්නොත්",
    "නම්ද", "ඇත්ත", "ඇත්තටම", "සැබෑ", "සැබවින්", "ඇත්තෙන්ම",
    "එකකි", "දෙකක්", "දෙක", "තුනක්", "තුන", "ටිකයි", "ටිකෙන්",
    "පොඩ්ඩක්", "පොඩ්ඩෙන්", "ටිකෙක්", "ටිකයක්",
    "අන්තිම", "මුල", "මුලින්", "මැද", "අග", "පළමු", "දෙවෙනි",
    "සමානව", "සමානයි", "එකවර", "එකවරම",
}

# --- Slang intensifiers / adjectives / evaluative words. Grammatically
# real Sinhala, but not the kind of neutral content noun real code-mixing
# substitutes — swapping "very"/"awesome"/"stupid"-type words for an
# English word is a different, much less naturalistic operation than
# substituting a noun (see codemix.py module docstring's design rationale:
# code-mixing is a WORD-CHOICE operation over content words). ---
_ADJECTIVE_INTENSIFIER = {
    "හරි", "පට්ට", "හෙන", "මහ", "මහා", "ලොකු", "පොඩි", "අමාරු", "කැත",
    "ලස්සන", "ලස්සනයි", "හොඳ", "හොද", "හොඳයි", "හොදයි", "හොඳම", "හොදම",
    "නරක", "නරකයි", "ලොකුම", "පොඩිම", "අඩුම", "වැඩිම", "වඩා", "වැඩි",
    "අඩු", "සුදු", "කලු", "රතු", "අලුත්", "පරණ", "නව", "පැරණි",
    "මෝඩ", "නාකි", "තඩි", "දුක", "සතුටු", "සතුටින්", "කනගාටු",
    "ලැජ්ජා", "ලැජ්ජයි", "බය", "බියගුල්", "ආසා", "ආසයි", "කැමති",
    "වෙනස්", "සමාන", "වැරදි", "නිවැරදි", "හරියට", "වැරදියට",
    "පුදුම", "පුදුමයි", "අමතක", "මතක", "මතකයි",
}

# --- Slurs, ethnic/caste slurs, and vulgar insults recurring in this
# hate-speech-labeled corpus. Flagged explicitly (not silently blanked) so
# the reason is visible: these are never appropriate substitution targets
# regardless of how the pipeline is tuned — see codemix_rejected_candidates.md's
# already-established precedent (මුස්ලිම් excluded on identical grounds). ---
_SLUR_SUBSTRINGS = (
    "ගොන", "හරක", "බූරු", "බැල්ල", "කුණු", "පකය", "පකෝ", "පොන්න",
    "හුත්ත", "හුජ්ජ", "පුක", "සක්කිලි", "වේසි", "වේස", "අවජාතක", "කාලකණ්ණි",
    "කාලකන්නි", "ජරාව", "ලූසර්", "ගැරි", "කැරි", "බයියා", "දෙමළෙක්",
    "සුද්දෙක්", "වඳුරු", "බල්ලෙක්", "බල්ලො", "බල්ලෝ", "බැල්ලී", "බැල්ලි",
    "බිජ්ජ", "බලු", "මුං", "පක", "මරු",
)

# --- Pronouns/case-marked pronoun forms the original + extra stoplist
# still missed (found via the freq>=10 manual audit batch). ---
_EXTRA_PRONOUNS = {
    "මා", "උබ", "උබට", "උබේ", "උබෙන්", "අපෙ", "තම", "ගේ", "ඊට", "මීට",
    "එ", "ය", "ස", "න්", "කෝ",
}

# --- Family/kinship terms — excluded as a CATEGORY, not case-by-case:
# these carry vocative/register risk (often diminutive, sarcastic, or
# affectionate address forms that don't map cleanly to a neutral English
# noun), the same caution already applied to the low-confidence-flagged
# දරුවා/ළමයා/බිරිඳ entries already in the lexicon — this list keeps that
# policy consistent instead of ad hoc per word. ---
_FAMILY_TERMS = {
    "අම්ම", "අම්මා", "අම්මට", "අම්මෝ", "පුතා", "පුතේ", "මල්ලි", "නංගි",
    "අයියා", "අයියේ", "තාත්තා", "මාමා", "නැන්දා", "අක්කා", "අක්කි",
    "මිත්‍රයෝ",
}

# --- Common verb roots and their frequent inflected surface forms —
# expanded from the freq>=10 manual audit. Sinhala verb morphology is
# open-class (any verb has ~10 forms), so this list is necessarily
# incomplete; it catches the small set of very-high-frequency verbs that
# dominate this corpus, not every verb. Combined with the suffix heuristic
# in mine_codemix_candidates.py. ---
_VERB_FORMS = {
    "ගිහින්", "ගිය", "ගියා", "ගියේ", "ගියම", "ගියත්", "යනවා", "යනව",
    "ඇවිත්", "ආවා", "ආවේ", "ආවෙ", "ආව", "ආ", "එන", "එනවා", "එනව",
    "අරන්", "අරං", "ගත්ත", "ගත්තා", "ගත්තේ", "ගන්නේ", "ගන්නෙ",
    "බලන්", "බලා", "බලාගෙන", "බලපු", "බලපන්", "දකින", "දැක්ක", "දැක්කම",
    "නොදකින්",
    "උන", "උනා", "උනාට", "උනත්", "උනේ", "උනාම", "වුනා", "වුනාට",
    "හිටියා", "හිටියේ", "හිටියෙ", "තිබ්බ", "තිබ්බා", "තිබුනා",
    "කරනව", "කරයි", "කරේ", "කළ", "කෙරුව", "කරමු", "කරද්දි",
    "කියනව", "කිව්ව", "කියයි", "කිව්වත්",
    "ගහන", "ගහනව", "ගහනවා", "කන", "කෑවා", "කෑ",
    "පලයන්", "හිතන්", "එලියට", "අයින්", "ඉවර", "ඉවරයි",
    "වෙයි", "වී", "විය", "වූ", "වන",
    "දුන්නා", "දුන්නේ", "දෙනවා", "දෙන",
}

# --- Abstract/idiomatic words that are grammatically nouns but function
# more like discourse particles or fixed-phrase fragments in actual usage
# (e.g. "කමක් නෑ" = "no worries", not "[issue] isn't-there") — not safe
# single-word substitution targets. ---
_IDIOMATIC_ABSTRACT = {
    "කරුම", "කරුමයක්", "කමක්", "ආතල්", "පව්", "තරම්", "බව", "කල්",
    "හැටි", "විදිහට", "විදියට", "දිහා", "මතක්", "ඉස්සර", "සාප", "අත",
    "වෙලාවට", "එදා", "ගමන්", "පාර", "පාරක්", "කාලේ", "කාලෙ", "කාලයක්",
}

# --- Genuine, common, but LOW real-world code-mix plausibility: basic
# everyday/traditional vocabulary (nature, food, body, household objects)
# that a bilingual Sinhala speaker would essentially never substitute with
# the English word in casual text — unlike modern/tech/institutional
# concepts (phone, government, president), which is where real code-mixing
# concentrates (see scripts/measure_codemix_rate.py's module docstring).
# Excluded on plausibility grounds, not because the translation is wrong. ---
_LOW_PLAUSIBILITY_CONCRETE = {
    "වතුර", "ගල්", "ගස්", "පොල්", "මල්", "තැන", "දවස්", "රෙදි", "රෙද්ද",
    "වචන", "කෑම", "බත්", "කිරි", "දිය", "අත", "කට", "ඇස්", "බඩ", "හිත",
    "ගෙවල්", "පණ", "ලේ", "තෙල්", "රස", "මස්", "ඇට",
}


def log(msg: str) -> None:
    print(f"[classify_codemix_candidates] {msg}")


def classify(word: str) -> str | None:
    """Returns a category tag, or None if the word survives to manual review."""
    if word in _EXTRA_FUNC or word in _EXTRA_PRONOUNS:
        return "func (function word/particle/pronoun — not a content-word target)"
    if word in _ADJECTIVE_INTENSIFIER:
        return "adjective/intensifier — not a typical code-mix noun target"
    if word in _FAMILY_TERMS:
        return "family/kinship term — excluded as a category (vocative/register risk)"
    if word in _VERB_FORMS:
        return "verb form — out of scope"
    if word in _IDIOMATIC_ABSTRACT:
        return "idiomatic/abstract — not a safe single-word substitution target"
    if word in _LOW_PLAUSIBILITY_CONCRETE:
        return "low real-world code-mix plausibility (basic/traditional vocabulary)"
    if any(root in word for root in _SLUR_SUBSTRINGS):
        return "slur/insult — not an appropriate substitution target"
    return None


def main() -> None:
    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    from collections import Counter
    tag_counts: Counter = Counter()
    n_manual = 0

    for row in rows:
        if row["prior_status"] != "new":
            continue  # previously-rejected rows keep their own note as-is
        if row["confidence_note"] and "likely verb" in row["confidence_note"]:
            continue  # already tagged by the mining script; leave as-is
        tag = classify(row["sinhala"])
        if tag is None:
            row["confidence_note"] = "needs_manual_review"
            n_manual += 1
        else:
            row["confidence_note"] = tag
            tag_counts[tag.split(" ")[0].split("(")[0].strip()] += 1

    for tag, count in tag_counts.most_common():
        log(f"auto-tagged {count}: {tag}")
    log(f"{n_manual} rows still need manual review")

    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "rank", "sinhala", "sold_frequency", "prior_status",
            "proposed_english", "confidence_note", "accept", "final_english",
        ])
        writer.writeheader()
        writer.writerows(rows)
    log(f"rewrote {CSV_PATH}")


if __name__ == "__main__":
    main()
