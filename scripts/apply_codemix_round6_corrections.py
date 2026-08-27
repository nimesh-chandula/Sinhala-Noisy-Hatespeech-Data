"""
Code-mix bank correction, round 6 — human review of the FULL 3,455-row
codemix_usage_review.csv (word bank + phrase bank together, round 5's
impact-ordered report). Same append-only correction mechanism rounds 1-4
established (data/lexicon/codemix_review_corrections.jsonl for word-bank
rows, codemix_phrase_review_corrections.jsonl for phrase-bank rows, action
"remove" or "correct"), applied at the scale of a genuinely complete
human pass rather than a targeted removal batch.

--- Source and parsing ---
data/lexicon/codemix_round6_corrections_raw.txt is the reviewer's raw
numbered-list submission, preserved verbatim for provenance. Format:
`<row_number>. <verdict>` where verdict is either "Remove" or a corrected
English rendering, usually `<English word/phrase> <romanized Sinhala
particle>` (e.g. row 4's "Country eka" -> the entry should read
"country එක"). The particle mapping below was built from precedent
already in the ACCEPTED wordbank/phrasebank (not invented) -- see
docs/research_documentation.md's round-6 write-up for the full derivation
and the specific rows each mapping was cross-checked against.

--- Special cases, resolved individually with the reviewer, not guessed ---
8 rows needed a resolution beyond the mechanical particle mapping (3
requests to change a SINHALA KEY rather than just the English side; one
apparent mismatch that turned out to be a genuine colloquial idiom once
checked against its firing context; a few particle spellings that a first
pass got wrong until cross-checked against the SPECIFIC row's own Sinhala
key rather than a generic frequency table). See _SPECIAL_CASES below and
the round-6 plan file for the full resolution reasoning for each.

Writes a reviewable report (data/lexicon/codemix_round6_corrections.csv,
same audit-trail spirit as round 4's codemix_removals_round4.csv) BEFORE
appending anything, then appends to both correction files and rebuilds
both banks. Idempotent: rows already appended by a prior run (tagged
"round6" in their note) are not appended again.

Run:  python scripts/apply_codemix_round6_corrections.py
"""

from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
LEXICON_DIR = REPO_ROOT / "data" / "lexicon"
RAW_PATH = LEXICON_DIR / "codemix_round6_corrections_raw.txt"
USAGE_CSV_PATH = LEXICON_DIR / "codemix_usage_review.csv"
REPORT_PATH = LEXICON_DIR / "codemix_round6_corrections.csv"
WORD_CORRECTIONS_PATH = LEXICON_DIR / "codemix_review_corrections.jsonl"
PHRASE_CORRECTIONS_PATH = LEXICON_DIR / "codemix_phrase_review_corrections.jsonl"
BUILD_WORDBANK = Path(__file__).resolve().parent / "build_codemix_wordbank.py"
BUILD_PHRASEBANK = Path(__file__).resolve().parent / "build_codemix_phrasebank.py"

NOTE_TAG = "round6"

# Romanized Sinhala grammatical particle -> Sinhala script, built from
# precedent already accepted in codemix_wordbank.jsonl/codemix_
# phrasebank.jsonl's own English fields (counted occurrences noted where
# relevant) -- see the plan file / module docstring for the derivation.
PARTICLE_MAP = {
    "eka": "එක", "ekak": "එකක්", "eke": "එකේ", "ekaka": "එකක", "ekakata": "එකකට",
    "ekata": "එකට", "eken": "එකෙන්",
    "la": "ලා", "lata": "ලාට", "lawa": "ලාව", "lage": "ලාගේ",
    "karanna": "කරන්න", "karala": "කරලා", "karanawa": "කරනවා", "karanne": "කරන්නේ",
    "kara": "කර", "karana": "කරන", "kranna": "කරන්න",  # kranna: typo for karanna
    "wela": "වෙලා", "wenna": "වෙන්න", "wenne": "වෙන්නේ", "wenawa": "වෙනවා",
    "kenek": "කෙනෙක්",
    "wala": "වල", "walata": "වලට", "walin": "වලින්", "walath": "වලත්",
    "ge": "ගේ", "da": "ද", "ma": "ම",
    "danna": "දාන්න", "wagayak": "වගයක්", "tika": "ටික",
    "ganna": "ගන්න", "gahala": "ගහලා", "una": "උනා", "yanna": "යන්න",
    "karagena": "කරගෙන",
}

# Rows whose resolution needed something beyond the mechanical particle
# map -- each entered by hand after checking the row's OWN current data
# (see docstring). action: "correct" (new english) | "remove" |
# "correct_new" (introduces a NEW sinhala key via a phrase-bank
# "correct" action, which supports keys that were never in the original
# translated worklist -- see build_codemix_phrasebank.py's merge logic).
_SPECIAL_CASES = [
    # row 435: add 2 real trigram extensions (checked against SOLD: පක්ෂය
    # occurs 4x, පක්ෂෙ 1x; පක්ෂේ occurs 0x, skipped -- would never fire).
    # Existing bigram left untouched.
    {"row": 435, "action": "correct_new", "kind": "phrase",
     "sinhala": "එක්සත් ජාතික පක්ෂය", "english": "united national party",
     "note": f"{NOTE_TAG}: row435 trigram extension (variant 1/2, occurs 4x in SOLD)"},
    {"row": 435, "action": "correct_new", "kind": "phrase",
     "sinhala": "එක්සත් ජාතික පක්ෂෙ", "english": "united national party",
     "note": f"{NOTE_TAG}: row435 trigram extension (variant 2/2, occurs 1x in SOLD)"},
    # row 1117: add new phrase-bank bigram (occurs 1x in SOLD); old
    # word-bank row left as-is (already plausible=false, dormant).
    {"row": 1117, "action": "correct_new", "kind": "phrase",
     "sinhala": "වර්ග දෙකයි", "english": "two types",
     "note": f"{NOTE_TAG}: row1117 promoted to phrase bigram, occurs 1x in SOLD"},
    # row 2777: casing fix only, same 3-word key.
    {"row": 2777, "action": "correct", "kind": "phrase",
     "sinhala": "නායක සජිත් ප්‍රේමදාස", "english": "opposition leader sajith premadasa",
     "note": f"{NOTE_TAG}: casing fix; 4-word විපක්ෂ extension not applied "
             "(_find_max_units has no 4-word match path)"},
    # row 3405: confirmed colloquial idiom (හිර = "tied down" ->
    # "married"), not literal "stuck", verified against its firing example.
    {"row": 3405, "action": "correct", "kind": "word",
     "sinhala": "හිර", "english": "marriage",
     "note": f"{NOTE_TAG}: confirmed idiom (හිර වෙනවා = get tied down/married) against firing example"},
    # row 1595: current sinhala ගේම් ගහලා already contains ගහලා -- direct match.
    {"row": 1595, "action": "correct", "kind": "phrase",
     "sinhala": "ගේම් ගහලා", "english": "games ගහලා",
     "note": f"{NOTE_TAG}: particle confirmed from row's own sinhala key"},
    # row 1402: current sinhala අවුට් උනා (not උනු).
    {"row": 1402, "action": "correct", "kind": "phrase",
     "sinhala": "අවුට් උනා", "english": "out උනා",
     "note": f"{NOTE_TAG}: particle confirmed from row's own sinhala key"},
    # row 1457: user overrode the auto-derived එත් reading -- applying
    # the original suggestion, Sinhala-script form of "walath".
    {"row": 1457, "action": "correct", "kind": "word",
     "sinhala": "ඊජිප්තුවෙත්", "english": "Egypt වලත්",
     "note": f"{NOTE_TAG}: reviewer-confirmed override of auto-derived reading"},
    # row 1694: reviewer confirmed "karan" against the fuller sentence
    # context (both firing examples continue "... හිතන් නැතුව/නෑ" -- a
    # negation the mined bigram doesn't capture); applied to the existing key.
    {"row": 1694, "action": "correct", "kind": "phrase",
     "sinhala": "දෙපාරක් හිතන්", "english": "twice think karan",
     "note": f"{NOTE_TAG}: reviewer-confirmed against fuller sentence context"},
]
_SPECIAL_CASE_ROWS = {c["row"] for c in _SPECIAL_CASES}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def parse_raw() -> list[tuple[int, str]]:
    """[(row_number, verdict_text), ...] from the raw numbered-list
    submission. Handles the observed 'N.', 'N ', and 'Nm ' (typo for 'N.')
    separators; splits on the NEXT number's start, not on any punctuation
    inside the verdict text itself (verdicts can contain periods, e.g.
    "I'm blocked.")."""
    raw = RAW_PATH.read_text(encoding="utf-8")
    pattern = re.compile(r"(?:^|\s)(\d{1,4})(\.|m(?=\s))?\s*")
    matches = list(pattern.finditer(raw))
    entries = []
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        text = raw[start:end].strip()
        entries.append((num, text))
    return entries


def _has_sinhala(text: str) -> bool:
    return any(0x0D80 <= ord(c) <= 0x0DFF for c in text)


def resolve_correction(text: str) -> str | None:
    """Non-special-case verdict text -> resolved English string, or None
    if it can't be mechanically resolved (shouldn't happen for anything
    not in _SPECIAL_CASE_ROWS, given the parse/cross-check already done --
    surfaced rather than silently guessed if it does)."""
    if _has_sinhala(text):
        return None  # direct sinhala-key edits are all special-cased above
    words = text.split()
    if not words:
        return None
    last = words[-1].lower().strip(".")
    if last in PARTICLE_MAP:
        base = " ".join(words[:-1])
        base = base[:1].lower() + base[1:] if base else base
        return f"{base.strip()} {PARTICLE_MAP[last]}"
    # plain english correction, no particle -- lowercase the leading word
    # to match the bank's overwhelming lowercase convention, leave the
    # rest as typed (preserves any deliberate proper-noun capitalization)
    return text[:1].lower() + text[1:]


def main() -> None:
    with USAGE_CSV_PATH.open(encoding="utf-8-sig") as f:
        usage_rows = list(csv.DictReader(f))

    entries = parse_raw()
    print(f"[round6] parsed {len(entries)} correction entries from {RAW_PATH.name}")

    report_rows = []
    corrections_by_file: dict[Path, list[dict]] = {WORD_CORRECTIONS_PATH: [], PHRASE_CORRECTIONS_PATH: []}

    for row_num, verdict in entries:
        if row_num > len(usage_rows):
            print(f"[round6] WARNING: row {row_num} exceeds usage CSV length ({len(usage_rows)}) -- skipped")
            continue
        usage_row = usage_rows[row_num - 1]
        kind = usage_row["kind"]
        sinhala = usage_row["sinhala"]
        target_path = WORD_CORRECTIONS_PATH if kind == "word" else PHRASE_CORRECTIONS_PATH

        if row_num in _SPECIAL_CASE_ROWS:
            for case in _SPECIAL_CASES:
                if case["row"] != row_num:
                    continue
                case_path = WORD_CORRECTIONS_PATH if case["kind"] == "word" else PHRASE_CORRECTIONS_PATH
                if case["action"] == "remove":
                    corrections_by_file[case_path].append(
                        {"sinhala": case["sinhala"], "action": "remove", "note": case["note"]})
                else:  # "correct" or "correct_new" both write a correct action
                    corrections_by_file[case_path].append({
                        "sinhala": case["sinhala"], "action": "correct",
                        "english": case["english"], "note": case["note"],
                    })
                report_rows.append({"row": row_num, "kind": case["kind"], "sinhala": case["sinhala"],
                                     "verdict": verdict, "resolved_action": "correct(special)",
                                     "resolved_english": case["english"], "note": case["note"]})
            continue

        if verdict.strip().lower().startswith("remove"):
            corrections_by_file[target_path].append(
                {"sinhala": sinhala, "action": "remove", "note": f"{NOTE_TAG}: full-review removal"})
            report_rows.append({"row": row_num, "kind": kind, "sinhala": sinhala, "verdict": verdict,
                                 "resolved_action": "remove", "resolved_english": "", "note": ""})
            continue

        resolved = resolve_correction(verdict)
        if resolved is None:
            print(f"[round6] WARNING: row {row_num} verdict {verdict!r} could not be mechanically "
                  "resolved and is not a special case -- SKIPPED, needs manual follow-up")
            report_rows.append({"row": row_num, "kind": kind, "sinhala": sinhala, "verdict": verdict,
                                 "resolved_action": "UNRESOLVED", "resolved_english": "", "note": "needs follow-up"})
            continue

        corrections_by_file[target_path].append({
            "sinhala": sinhala, "action": "correct", "english": resolved,
            "note": f"{NOTE_TAG}: full-review correction",
        })
        report_rows.append({"row": row_num, "kind": kind, "sinhala": sinhala, "verdict": verdict,
                             "resolved_action": "correct", "resolved_english": resolved, "note": ""})

    with REPORT_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["row", "kind", "sinhala", "verdict",
                                                "resolved_action", "resolved_english", "note"])
        writer.writeheader()
        writer.writerows(report_rows)
    print(f"[round6] wrote review report -> {REPORT_PATH} ({len(report_rows)} rows)")

    n_unresolved = sum(1 for r in report_rows if r["resolved_action"] == "UNRESOLVED")
    if n_unresolved:
        print(f"[round6] {n_unresolved} row(s) unresolved -- see {REPORT_PATH.name}, NOT appended, stopping short of applying")
        sys.exit(1)

    for path, rows in corrections_by_file.items():
        if not rows:
            continue
        already = set()
        for existing in _load_jsonl(path):
            if NOTE_TAG in existing.get("note", ""):
                already.add((existing["sinhala"], existing["action"], existing.get("english", "")))
        to_append = [r for r in rows if (r["sinhala"], r["action"], r.get("english", "")) not in already]
        skipped = len(rows) - len(to_append)
        if skipped:
            print(f"[round6] {path.name}: {skipped} already appended by a prior run -- skipping")
        if to_append:
            with path.open("a", encoding="utf-8") as f:
                for r in to_append:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
            print(f"[round6] appended {len(to_append)} correction(s) -> {path.name}")

    print("[round6] rebuilding word bank...")
    result = subprocess.run([sys.executable, str(BUILD_WORDBANK)], cwd=str(REPO_ROOT))
    if result.returncode != 0:
        sys.exit(result.returncode)
    print("[round6] rebuilding phrase bank...")
    result = subprocess.run([sys.executable, str(BUILD_PHRASEBANK)], cwd=str(REPO_ROOT))
    if result.returncode != 0:
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()
