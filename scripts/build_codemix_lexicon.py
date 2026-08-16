"""
Phase 3 step 2 — build the Sinhala -> English code-mixing substitution
lexicon. Unlike scripts/build_word_variants.py (which derives its variants
mechanically from a 7.1M-row attested-spelling table), this lexicon is
HAND-CURATED: there is no Sinhala-English translation dataset anywhere in
this repo (see docs/research_documentation.md §2), so every entry below
was chosen and verified by hand, the same discipline used for the 123-entry
loanword table in src/romanizers/aksharamukha.py.

--- The attestation rule (why each entry is here, not just plausible) ---
A Sinhala surface form is admitted only if:
  1. it is frequent enough in SOLD to matter for coverage, AND
  2. the proposed English substitution is ACTUALLY ATTESTED as real
     Singlish usage, via one of three evidence channels measured by
     scripts/measure_codemix_rate.py (data/lexicon/codemix_reference_stats.json):
       (a) LOANWORD  — the Sinhala form is itself a phonetic Sinhala-script
           spelling of the English word (e.g. "බස්" = "bus"). The 123-entry
           table in src/romanizers/aksharamukha.py is the primary source;
           a handful of additional loanwords this project's own frequency
           scan surfaced (බස්/ගේම්/ටීම්/චැනල්/සීන්) are added directly here
           rather than retroactively edited into that Phase-2 file, to
           avoid re-triggering Phase 2's already-locked verification.
       (b) LATIN_TOKEN — the English word appears as a Latin-script token
           in real Singlish (reference_singlish.txt or cleaned SOLD) that
           survives the negative-filter measurement (candidate_english_vocabulary).
       (c) EKA_CONSTRUCTION — the STRONGEST evidence: the English word was
           observed directly attached to a Sinhala "එක" case particle in
           SOLD's own raw text (eka_construction_vocabulary) — i.e. this
           exact grammatical construction, not just "this word exists
           somewhere". 555 such instances across 345 distinct English
           stems were found.
  3. a human (this session, then the project owner) verified the pairing
     actually means what it claims and isn't a false-friend collision —
     e.g. "ගෑණි" (woman/wife, frequently used pejoratively in this
     hate-speech corpus) was considered and REJECTED because a blind
     "wife" substitution would misrepresent most of its actual uses. Every
     rejected candidate is recorded with its reason in
     data/lexicon/codemix_rejected_candidates.md, mirroring the loanword
     table's exclusion list.

--- Morphology: why keys are exact inflected surface forms ---
Sinhala is agglutinative; case lives in suffixes attached to the noun stem
via the light noun "එක" ("book" + dative -> "book එකට", NOT a romanized
"eka"). This is a real, productive, and common pattern in this exact
corpus (555 measured instances). So CURATED_NATIVE_ENTRIES keys the exact
inflected Sinhala surface forms actually observed in SOLD (e.g. "ආණ්ඩුව",
"ආණ්ඩුවේ", "ආණ්ඩුවට" are three separate entries, not one lemma with
runtime inflection) — the noiser never does morphological analysis, only
verified surface substitution, exactly like build_word_variants.py's
attested-spelling approach.

Some entries here have LOW SOLD frequency (1-2 occurrences) despite solid
evidence for the English side (e.g. "පින්තූරය"/"photo": the "photo එක"
construction is well-attested (7x) but the specific native Sinhala noun
for "photo" is rare in this corpus, since posters mostly already write
"photo" directly). These are kept for correctness/completeness but
contribute little to noiser coverage — documented, not hidden.

--- A second expansion pass, and what it found ---
The first pass (127 loanword + 34 native entries) covered only 1.27% of
SOLD's Sinhala word tokens — below even the measured "light" natural rate.
Two more mining rounds were run to close that gap:
  1. An automated CER-based scan: every SOLD word's canonical romanization
     compared against a ~340-word pool of social/tech/political English
     terms, keeping close matches (CER <= 0.34) for hand review. This is
     the SAME method LOG.md already documented as producing majority false
     positives when used to pick the answer automatically (e.g. "සඳ" (moon)
     -> "scandal", "පොතේ" (in the book) -> "mother") — used here strictly as
     a CANDIDATE GENERATOR, with every survivor individually verified
     against its real meaning before inclusion, never auto-accepted.
  2. A deeper pass through SOLD's frequency ranking (positions 400-900,
     beyond the first pass's top-400) surfacing more directly-observed
     Sinhala-script loanword spellings (ෆොටෝ/පොටෝ="photo", වීඩියෝ="video",
     ට්වීට්="tweet", මැසේජ්="message", ...).

For LOANWORD-type entries specifically, note the verification standard is
different from native-word entries: the evidence is direct phonetic/
orthographic reading (does this Sinhala spelling render this English word
when sounded out, per standard Sinhala phonology?) plus SOLD frequency for
coverage relevance — NOT the three-channel measurement above, which exists
to ground the CHOICE of English gloss for a native word's translation
(where multiple glosses are plausible and need real-usage evidence to pick
correctly). A loanword spelling has only one correct decoding, so a
human reading it is authoritative in a way corpus statistics can't
improve on — this is exactly how the original 123-entry table was built.
One direct consequence: "video" and "message" are included as verified
overrides despite scoring 0 in candidate_english_vocabulary — both are
coincidental Swa-Bhasha collisions (the same false-negative class the
measurement script's docstring already documents), not real absence; other,
independent evidence (a prior manual sample of reference_singlish.txt found
"video" as its single most frequent English-looking token, 149 occurrences)
confirms these are genuine, common loanwords, not noise.

Even after both expansion passes, combined coverage lands at ~1.8% of
SOLD's Sinhala tokens — barely above the first pass, not the order-of-
magnitude jump a "heavy" severity target would need. This is not a
shortfall in effort: it converges here because this pass is mining the
SAME corpus for the SAME phenomenon scripts/measure_codemix_rate.py
already measured at ~1.5-1.8% natural token rate. A rigorously-sourced
lexicon and the natural rate necessarily agree, because they're both
reading off the same underlying behavior. Pushing coverage meaningfully
higher would require abandoning the attestation standard, not applying it
harder — this finding is reported back for a human decision on how
light/heavy severity should be defined given it, not resolved silently
here.

Run:  python scripts/build_codemix_lexicon.py
Writes:
  data/lexicon/codemix_lexicon.jsonl — {"sinhala", "english", "source",
    "sold_frequency", "evidence"} one line per verified entry
  data/lexicon/codemix_rejected_candidates.md — every candidate considered
    and excluded, with the reason
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402
from src.romanizers.aksharamukha import _LOANWORD_OVERRIDES  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
SOLD_DIR = DATA_DIR / "sold"
LEXICON_DIR = DATA_DIR / "lexicon"
OUTPUT_PATH = LEXICON_DIR / "codemix_lexicon.jsonl"
REJECTED_PATH = LEXICON_DIR / "codemix_rejected_candidates.md"

# --- (a) Additional loanword-type entries: Sinhala-script phonetic
# spellings of English words, found via this project's own SOLD frequency
# scan (not yet in aksharamukha.py's table — see module docstring for why
# they're kept separate rather than merged into that Phase-2 file). ---
_EXTRA_LOANWORDS = {
    "බස්": "bus",       # SOLD freq 120 — extremely common; "bus" itself
    "ගේම්": "game",      # SOLD freq 12; eka-construction "game" also attested (2)
    "ටීම්": "team",      # SOLD freq 14; latin-token "team" attested (6)
    "චැනල්": "channel",  # SOLD freq 17; eka-construction "channel" attested (2)
    "සීන්": "scene",     # SOLD freq 66 — very common Sri Lankan slang for "scene"
    # --- second pass: CER-scan candidates, each individually verified by
    # reading the actual Sinhala spelling, not auto-accepted (see module
    # docstring — the same method previously produced majority false
    # positives when used without this discipline) ---
    "පෝස්ට්": "post", "පොස්ට්": "post",  # two attested spellings of "post"
    "ෆිල්ම්": "film", "මාස්ක්": "mask", "චැට්": "chat", "ජොබ්": "job",
    "ටෙස්ට්": "test", "හොටෙල්": "hotel", "හෝටල්": "hotel", "එඩිට්": "edit",
    "ෆන්": "fan", "ලැප්ටොප්": "laptop",
    "හොස්පිට්ල්": "hospital", "හොස්පිටල්": "hospital", "ඩ්‍රාමා": "drama",
    "කැමරා": "camera", "ට්‍රැෆික්": "traffic", "ෆැමිලි": "family",
    "ට්‍රේන්": "train", "මෝනින්": "morning", "ස්ටේටස්": "status",
    "සෙල්ෆි": "selfie", "බොස්": "boss",
    "පොලිසිය": "police", "පොලීසිය": "police",  # inflected forms of the existing පොලිස්->police
    "ගෝල්": "goal", "බුක්": "book", "බැංකු": "banks", "ඩේටා": "data",
    "රිපෝට්": "report",
    # --- third pass: SOLD frequency ranks 400-900, direct loanword spellings ---
    "ෆොටෝ": "photo", "පොටෝ": "photo",  # two attested spellings of "photo"
    "ට්වීට්": "tweet", "ට්විටර්": "twitter", "ටෝක්": "talk", "කෝල්": "call",
    "මැච්": "match", "කැම්පස්": "campus", "මැසේජ්": "message",
    "නිවුස්": "news",  # alt spelling of the existing නිව්ස්->news
    # "video" and "message" score 0 in codemix_reference_stats.json's
    # candidate_english_vocabulary — a coincidental Swa-Bhasha collision
    # (the measurement script's own documented false-negative class), not
    # real absence. Independent evidence: a prior manual sample of
    # reference_singlish.txt found "video" as its single most frequent
    # English-looking token (149 occurrences). Included as a verified
    # override, same as the loanword table's existing entries.
    "වීඩියෝ": "video",
}

# --- (b)/(c) Hand-curated native-word entries. Each tuple is
# (sinhala_surface_form, english_substitution, evidence_note). See the
# module docstring for the attestation rule these all satisfy, and
# data/lexicon/codemix_rejected_candidates.md for what was excluded and why. ---
CURATED_NATIVE_ENTRIES: list[tuple[str, str, str]] = [
    # --- love (bare; used predicatively/exclamatorily in Sinhala too, so
    # no eka-particle construction needed) ---
    ("ආදරේ", "love", "latin_token(love)=23; colloquial form"),
    ("ආදරය", "love", "latin_token(love)=23; formal form"),

    # --- media / government / institutional vocabulary (bare nouns read
    # naturally without the eka particle in these roles) ---
    ("මාධ්‍ය", "media", "latin_token(media)=9"),
    ("ජනාධිපති", "president", "latin_token(president)=6"),
    ("ජනාධිපතිතුමා", "president", "latin_token(president)=6; drops honorific, natural in casual Singlish"),
    ("ඇමති", "minister", "SOLD freq 44; plausible, moderate confidence (no direct latin-token hit)"),
    ("ඇමතිතුමා", "minister", "SOLD freq 5; drops honorific"),

    # --- government (eka-construction extrapolated: the eka-particle
    # pattern is a general, productive Sinhala-Singlish rule validated by
    # 555 independent instances across 345 other English stems, not
    # word-specific, so applying it to an unseen-but-attested word like
    # "government" is a reasonable generalization of an established rule) ---
    ("ආණ්ඩුව", "government එක", "latin_token(government)=4; eka-particle pattern extrapolated"),
    ("ආණ්ඩුවේ", "government එකේ", "locative form"),
    ("ආණ්ඩුවට", "government එකට", "dative form"),

    # --- voting / political process ---
    ("ඡන්දය", "vote එක", "latin_token(vote)=2,(votes)=5"),
    ("ඡන්දයක්", "vote එකක්", "indefinite form"),
    ("වර්ජනය", "strike එක", "latin_token(strike)=4"),
    ("මැතිවරණය", "election එක", "latin_token(election)=1 — LOW CONFIDENCE, flagged for review"),

    # --- life / people ---
    ("ජීවිතය", "life එක", "latin_token(life)=8; eka_construction(life)=2"),
    ("ජීවිතයක්", "life එකක්", "indefinite form"),
    ("ජනතාව", "people", "latin_token(people)=8"),

    # --- family ---
    ("දරුවා", "child", "latin_token(child)=1 — LOW CONFIDENCE; sensitive term, flagged for review"),
    ("ළමයා", "child", "colloquial synonym of දරුවා; same confidence note"),
    ("දරුවෝ", "children", "latin_token(children)=3"),
    ("බිරිඳ", "wife", "latin_token(wife)=1 — LOW CONFIDENCE, flagged for review"),
    ("යාළුවා", "friend", "latin_token(friend)=5"),
    ("මිත්‍රයා", "friend", "formal synonym of යාළුවා"),
    ("යාළුවෝ", "friends", "plural form"),

    # --- money (high SOLD frequency, high real-world plausibility, but
    # low measured latin-token attestation — flagged, not silently trusted) ---
    ("සල්ලි", "money", "SOLD freq 185; latin_token(money)=2 — MODERATE CONFIDENCE, low attestation count, flagged for review"),
    ("මුදල්", "money", "SOLD freq 30; more formal synonym of සල්ලි, same target"),

    # --- social (political/media commentary register) ---
    ("සමාජ", "social", "latin_token(social)=6"),
    # ජීවිතේ: colloquial alternate spelling of ජීවිතය (definite -ය/-ේ pair;
    # both are real, independently common surface forms in SOLD)
    ("ජීවිතේ", "life එක", "SOLD freq 45; colloquial spelling of ජීවිතය"),

    # --- items independently attested via the eka-construction channel,
    # but where the native Sinhala noun itself is rare in SOLD (kept for
    # correctness; minimal coverage contribution — see module docstring) ---
    ("පින්තූරය", "photo එක", "eka_construction(photo)=7; native form rare in SOLD (freq 1)"),
    ("පින්තූරයක්", "photo එකක්", "indefinite form"),
    ("විවාහය", "wedding එක", "eka_construction(wedding)=6"),
    ("ගීතය", "song එක", "eka_construction(song)=4"),
    ("ගීතයක්", "song එකක්", "indefinite form"),
    ("පත්‍රය", "paper එක", "eka_construction(paper)=3; native form rare in SOLD (freq 1)"),
    ("සමූහය", "group එක", "eka_construction(group)=4; native form rare in SOLD (freq 2)"),
    ("සේවාව", "service එක", "eka_construction(service)=2; native form rare in SOLD (freq 1)"),

    # --- world ---
    ("ලෝකයේ", "world එකේ", "latin_token(world)=6; locative form"),
    ("ලෝකය", "world එක", "bare/definite form"),
    ("ලෝකෙ", "world එක", "colloquial short form of ලෝකය"),

    # --- vaccine / comment (semantic nuance noted) ---
    ("එන්නත", "vaccine එක", "latin_token(vaccine)=3; eka_construction(vaccine)=2"),
    ("අදහස", "comment", "latin_token(comment)=10; SEMANTIC NUANCE: literal meaning is 'opinion/idea', mapped to social-media 'comment' sense — flagged for review"),
    ("අදහසක්", "comment එකක්", "indefinite form"),
]


def log(msg: str) -> None:
    print(f"[build_codemix_lexicon] {msg}")


def sold_word_frequency() -> dict[str, int]:
    """{sinhala_surface_form: count} across SOLD train+test."""
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


def main() -> None:
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)
    freq = sold_word_frequency()

    entries: list[dict] = []
    seen_keys: set[str] = set()

    # (a) the full Phase-2 loanword table, reused directly — see module
    # docstring for why the direction here (bypass phonetic Sinhala
    # spelling, substitute the English spelling) is exactly what a
    # code-mixing noiser wants.
    for sinhala, english in _LOANWORD_OVERRIDES.items():
        f = freq.get(sinhala, 0)
        if f == 0:
            continue  # not present in SOLD at all — no coverage value, skip
        entries.append({
            "sinhala": sinhala, "english": english, "source": "loanword",
            "sold_frequency": f, "evidence": "src.romanizers.aksharamukha._LOANWORD_OVERRIDES (Phase 2, hand-verified)",
        })
        seen_keys.add(sinhala)

    # (a) extra loanwords found by this phase's own scan
    for sinhala, english in _EXTRA_LOANWORDS.items():
        if sinhala in seen_keys:
            continue
        f = freq.get(sinhala, 0)
        entries.append({
            "sinhala": sinhala, "english": english, "source": "loanword",
            "sold_frequency": f, "evidence": "Phase 3 frequency scan, hand-verified",
        })
        seen_keys.add(sinhala)

    # (b)/(c) curated native-word entries
    dupes = []
    for sinhala, english, note in CURATED_NATIVE_ENTRIES:
        if sinhala in seen_keys:
            dupes.append(sinhala)
            continue
        f = freq.get(sinhala, 0)
        entries.append({
            "sinhala": sinhala, "english": english, "source": "native",
            "sold_frequency": f, "evidence": note,
        })
        seen_keys.add(sinhala)
    if dupes:
        log(f"WARNING: {len(dupes)} curated entries duplicate a loanword key, skipped: {dupes}")

    entries.sort(key=lambda e: -e["sold_frequency"])
    total_occurrences = sum(e["sold_frequency"] for e in entries)
    total_sold_words = sum(freq.values())
    log(f"{len(entries)} lexicon entries ({sum(1 for e in entries if e['source']=='loanword')} loanword, "
        f"{sum(1 for e in entries if e['source']=='native')} native)")
    log(f"combined lexicon covers {total_occurrences} SOLD word-token occurrences "
        f"({total_occurrences / total_sold_words:.4%} of all {total_sold_words} Sinhala word tokens)")

    with OUTPUT_PATH.open("w", encoding="utf-8") as f_out:
        for e in entries:
            f_out.write(json.dumps(e, ensure_ascii=False) + "\n")
    log(f"wrote {len(entries)} entries -> {OUTPUT_PATH}")

    write_rejected_candidates()
    log(f"wrote rejected-candidates record -> {REJECTED_PATH}")


def write_rejected_candidates() -> None:
    lines = [
        "# Code-mixing lexicon — rejected candidates",
        "",
        "Every Sinhala word considered for the code-mixing lexicon "
        "(scripts/build_codemix_lexicon.py) and explicitly excluded, with "
        "the reason. Mirrors the exclusion-list discipline used for the "
        "Phase 2 loanword table in src/romanizers/aksharamukha.py.",
        "",
        "| Sinhala | Considered English | Reason excluded |",
        "|---|---|---|",
        "| වැඩ / වැඩක් / වැඩේ | work / job | Too idiomatically overloaded — most real uses are slang for 'the situation/matter', not literally 'work'; blind substitution would misrepresent most occurrences. |",
        "| කතා / කතාව | talk / story | Meaning too broad/context-dependent for a safe single-target substitution. |",
        "| ගෑණි | wife / woman | Frequently used pejoratively in this hate-speech corpus to mean 'woman' generically, not specifically 'wife' — high risk of mistranslating the actual sense. |",
        "| ගෙදර | home | 'home' has ZERO attestation in the measured candidate vocabulary (all 3 evidence channels) despite being independently plausible — excluded per the attestation rule rather than trusted on intuition alone. |",
        "| රට / රටේ / රටට / රටක් | country | 'country' has zero attestation in the measured candidate vocabulary; excluded per the attestation rule. |",
        "| ලංකාව / ලංකාවේ / ලංකාවෙ | Sri Lanka / Lanka | Proper noun — not a meaningful translation target for a code-mixing substitution. |",
        "| ප්‍රශ්නය / ප්‍රශ්නයක් | problem | 'problem' has zero attestation in the measured candidate vocabulary; excluded per the attestation rule despite being independently plausible. |",
        "| පක්ෂය | party (political) | Ambiguous with 'party' (celebration) sense, which IS already a verified loanword (පාටි -> party) — substituting the political sense as bare 'party' risks being misread as the celebration sense, especially in political-commentary posts. |",
        "| හිතන | thinking | Verb form — out of scope; this lexicon only performs verified NOUN surface substitutions, never morphological/verb analysis. |",
        "| ගින්න | fire | Common Sinhala slang for 'angry/heated', not literally 'fire', in many real uses — polysemy risk, and low attestation. |",
        "| දෙයක් / දේ / දේවල් | thing(s) | Too abstract/pronoun-like; not a concrete content-word substitution. |",
        "| මිනිස්සු / මිනිස්සුන්ට | people | Redundant with ජනතාව -> people (already included); mixing both risks inconsistent output for near-synonyms. |",
        "| කණ්ඩායම | team | SOLD frequency only 2 — negligible coverage value, and ටීම් (a direct Sinhala-script loanword for 'team', freq 14) already covers this concept more naturally. |",
        "| චිත්‍රපටය | film | Zero attestation in SOLD at any inflection — casual Singlish doesn't use this formal word. |",
        "| දුරකථනය | phone | Zero attestation in SOLD — casual speech has no separate native word for this; posters already just write 'phone'/'fone' directly, so there is no native form to substitute FROM. |",
        "| උසාවිය | court | SOLD frequency only 1 — too rare to be worth the entry. |",
        "| විරෝධතාව | protest | Zero occurrences of this exact form in SOLD. |",
        "| ජනතාවගේ | people's | Grammatically awkward as a possessive English substitution; skipped even though the base noun ජනතාව is included. |",
        "| මුස්ලිම් | muslim | Genuine, common loanword spelling (SOLD freq 59) — excluded anyway on purpose: this is a religious/ethnic identity term in a HATE-SPEECH-labeled corpus, and substituting identity markers inside potentially hateful sentences is a different, higher-risk kind of change than a neutral institutional/tech noun. Out of scope for a spelling/script-choice noiser regardless of frequency. |",
        "| සඳ | scandal | 'සඳ' means 'moon' (common, poetic native word) — a coincidental CER-match false positive from the automated candidate scan, not scandal. |",
        "| පොතේ | mother | 'පොතේ' means 'in the book' (පොත=book + locative) — false positive from the automated scan. |",
        "| වේසිගෙ / වේසිගේ / වේසියේ | website | 'වේසිය' means 'prostitute' — a common slur in this corpus, not 'website'. The automated CER scan matched these purely on spelling; substituting a slur for 'website' would have been both wrong and a serious meaning-preservation failure. Flagged here explicitly given how easily this one could have slipped through on spelling alone. |",
        "| ලෙඩේ / ලෙඩෙක් | leader | 'ලෙඩ' means 'sick/illness' (common slang for 'annoying person') — false positive from the automated scan. |",
        "| පෝලිම් / පෝලිමේ | police | 'පෝලිම' means 'queue/line' — false positive from the automated scan; easily confused with the genuine පොලිසිය->police entry that IS included. |",
        "| ගම් / ගමේ | game | 'ගම'='village' is one of the most common native Sinhala words in the corpus — false positive from the automated scan; genuine 'game' is covered instead via ගේම් (an unambiguous phonetic loanword spelling). |",
        "| චාමර | camera | This is a common Sinhala given name (Chamara), not the word for 'camera' — false positive from the automated scan; genuine 'camera' is covered via කැමරා instead. |",
        "| (~35 further automated-scan matches) | various | Rejected in bulk: pronouns/particles/verb-inflections that happen to romanize close to an English word (e.g. මට='to me'->'data', ට='to'->'tea', දාලා='having put'->'data'), the same false-positive class LOG.md already documented for the original loanword table. Not enumerated individually — none had a plausible correct English reading, unlike the entries above which are recorded because the false positive was specific and instructive. |",
        "",
        "Low-confidence entries that WERE included (not rejected) but are "
        "flagged for extra scrutiny during human review: ඇමති/ඇමතිතුමා "
        "(minister — no direct latin-token attestation, plausibility-based), "
        "සල්ලි/මුදල් (money — high plausibility but latin-token count only 2), "
        "දරුවා/ළමයා/බිරිඳ (child/wife — latin-token count 1), අදහස "
        "(comment — semantic nuance from 'opinion' to 'comment'), මැතිවරණය "
        "(election — latin-token count 1), වීඩියෝ/මැසේජ් (video/message — "
        "verified overrides for a measurement-tool false negative, see module docstring).",
    ]
    REJECTED_PATH.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
