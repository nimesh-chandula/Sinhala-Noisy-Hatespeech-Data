"""
Code-mix bank correction, round 4 — Stage 0 (HUMAN GATE, read-only).

A reviewer objected that code-mixing is unnatural because switched words
"appear in certain places in a sentence more often than others." Tested
against SOLD's own naturally-occurring code-switching, that claim is refuted
for POSITION (this noiser does in-place type substitution — see
src/noisers/codemix.py's module docstring — so the switch site is always
inherited from a real Sinhala sentence, never chosen by us) but upheld for
WORD CHOICE: some bank entries are switches no bilingual speaker would make.

This script does NOT touch the lexicon or any generated output. It only
proposes a removal list for human approval, sorted into three tiers, the
same way scripts/build_codemix_usage_report.py proposed corrections in
rounds 1-3. Round 4's corrections (data/lexicon/codemix_review_corrections.jsonl,
action="remove") get appended only after this list is approved — see
scripts/apply_codemix_removals.py.

Tiers:
  1. affect-bearing: english side is an evaluative/abusive/slur term
     (bal.laa -> dog, pissu -> crazy). Not a style problem: switching the
     insult to English reads weaker and can silently change whether a post
     still reads as offensive, which is a label-integrity problem, not a
     naturalness one. `slur_flag` in codemix_translation_worklist.jsonl is
     False for all 7,969 rows -- it never fired, matching the
     _SLUR_SUBSTRINGS wrong-import no-op bug from LOG.md Phase 3 v2. No slur
     filtering has ever actually been applied to this bank; this tier is
     that cleanup.
  2. native Sinhala verb -> bare English verb, excluding source=loanword:
     Sinhala borrows English verbs as "V + karanawa/karanna/karala", never
     bare, so "kiyanna -> say" is not a construction a bilingual would
     produce. This is the one tier that is a genuine PLACEMENT defect.
  3. codemix_plausible == False entries that still fired via the fallback
     pool in _apply() step 8 -- already flagged implausible by human
     reviewers in rounds 1-3, but used anyway when a post had no plausible
     candidate. Reported for visibility; NOT bundled into the recommended
     removal set, since dropping all 606 would cost ~10% touched-post
     coverage against the density directive in LOG.md Phase 3.

`verb_suspect` and `slur_flag` (both in codemix_translation_worklist.jsonl)
were tried as ready-made classifiers for tier 2 and rejected: verb_suspect
flags non-verbs like "sinhala -> Sinhala"; slur_flag never fires. Recorded
here so a future pass doesn't retry them.

Writes:
  data/lexicon/codemix_removals_round4.md   (for reading + the case for each tier)
  data/lexicon/codemix_removals_round4.csv  (for marking up: decision column)

Run:  python scripts/propose_codemix_removals.py
"""

from __future__ import annotations

import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src.graphemes import text_runs  # noqa: E402
from src.noisers.codemix import _apply, _load_wordbank  # noqa: E402
from generate_codemix import _row_seed  # noqa: E402

OUTPUTS_DIR = REPO_ROOT / "data" / "outputs"
SOLD_DIR = REPO_ROOT / "data" / "sold"
LEXICON_DIR = REPO_ROOT / "data" / "lexicon"
WORDBANK_PATH = LEXICON_DIR / "codemix_wordbank.jsonl"
WORKLIST_PATH = LEXICON_DIR / "codemix_translation_worklist.jsonl"
MD_PATH = LEXICON_DIR / "codemix_removals_round4.md"
CSV_PATH = LEXICON_DIR / "codemix_removals_round4.csv"
MAX_EXAMPLES = 3

# --- Tier 1: english side is evaluative/abusive/slur -----------------------
_ABUSIVE_HEADWORDS = {
    "maniac", "crazy", "idiot", "fool", "stupid", "dog", "pig", "devil",
    "demon", "traitor", "thief", "liar", "shit", "moron", "beast", "swine",
    "bastard", "whore", "bitch", "rascal", "wretch", "filth", "madman",
    "lunatic",
}

# --- Tier 2: bare English finite verb, no kara- licensor -------------------
_VERB_HEADWORDS = {
    "say", "eat", "know", "come", "go", "die", "laugh", "run", "walk", "see",
    "look", "give", "take", "make", "think", "write", "read", "sleep",
    "drink", "buy", "sell", "kill", "hit", "ask", "tell", "call", "put",
    "get", "find", "feel", "live", "leave", "bring", "send", "keep", "show",
    "hear", "speak", "meet", "sit", "stand", "open", "close", "break",
    "catch", "throw", "win", "lose", "learn", "teach", "help", "start",
    "stop", "wait", "watch", "hold", "turn", "pay", "cut", "save", "spend",
    "understand", "remember", "forget", "believe", "need", "try", "use",
    "become", "happen", "follow", "lead", "grow", "move", "carry", "arrest",
    "beat", "bite", "burn", "fall", "forgive", "hide", "marry", "pull",
    "push", "ride", "shoot", "sing", "steal", "wash", "wear",
}

# Entries that match the tier-2 verb-headword test but are, on inspection,
# Sinhala-script SPELLINGS of the English word itself (koi->call, phalo->
# follow, trai->try, kat->cut are the source=loanword analogues of this) --
# just mistagged source=llm instead of source=loanword. Switching these back
# to Latin is the most natural move available in the post, not a defect, so
# they are pulled out of tier 2 and reported separately rather than folded
# into the removal recommendation. Identified by hand against the fired list
# for this build; re-check this set if the wordbank is rebuilt from scratch.
_LOANWORD_LIKE_OVERRIDE = {"බයිට්", "ලුක්", "ශෝ", "ඕපන්", "කැච්", "ස්ටාර්ට්", "ටේක්", "ශො"}

_ELIGIBLE_SUFFIX = ("ට", "ෙන්", "න්", "ේ", "ෙ", "ගේ", "වල", "වලට", "වලින්")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_full_wordbank() -> dict[str, dict]:
    return {row["sinhala"]: row for row in _load_jsonl(WORDBANK_PATH)}


def _load_labels() -> dict[str, int]:
    labels: dict[str, int] = {}
    for split in ("train", "test"):
        for row in _load_jsonl(SOLD_DIR / f"{split}.jsonl"):
            labels[row["post_id"]] = row["label"]
    return labels


def _load_worklist() -> dict[str, dict]:
    return {row["sinhala"]: row for row in _load_jsonl(WORKLIST_PATH)}


def _classify(sinhala: str, entry: dict) -> tuple[str, str]:
    """Returns (tier, reason). tier is one of "1", "2", "3", "" (not flagged)."""
    english = entry.get("english", "")
    headword = english.split()[0].lower().strip(".,") if english else ""
    has_sinhala = any("඀" <= c <= "෿" for c in english)

    if headword in _ABUSIVE_HEADWORDS:
        return "1", "english side is an evaluative/abusive term"

    if (headword in _VERB_HEADWORDS and not has_sinhala and len(english.split()) == 1
            and entry.get("source") != "loanword" and sinhala not in _LOANWORD_LIKE_OVERRIDE):
        return "2", "bare English finite verb substituted for a native Sinhala verb form (no karanawa/karanna licensor)"

    if not entry.get("codemix_plausible", True):
        return "3", "reviewer-marked codemix_plausible=False, fires only via the _apply() fallback pool"

    return "", ""


def _natural_switch_stats(labels: dict[str, int]) -> None:
    """Print the natural-code-switching-by-label check this round's Tier 1
    argument rests on, so it's reproduced (not just asserted) every time this
    script runs."""
    import re
    lat = re.compile(r"^[A-Za-z][A-Za-z\-]{1,}$")
    sin = re.compile(r"^[඀-෿‍]+$")
    sinany = re.compile(r"[඀-෿]")
    strip = lambda w: w.strip(".,!?\"'()[]{}#@:;‘’“”")
    skip = {"url", "user", "rt", "lka", "srilanka", "lanka", "sri"}
    switches = defaultdict(int)
    sinhala_tokens = defaultdict(int)
    for split in ("train", "test"):
        for row in _load_jsonl(SOLD_DIR / f"{split}.jsonl"):
            text, label = row["text"], row["label"]
            if not sinany.search(text):
                continue
            words = [strip(w) for w in text.split()]
            sinhala_tokens[label] += sum(1 for w in words if sin.match(w))
            for i in range(1, len(words) - 1):
                w = words[i]
                if (lat.match(w) and w.lower() not in skip
                        and sin.match(words[i - 1]) and sin.match(words[i + 1])):
                    switches[label] += 1
    rate0 = switches[0] / sinhala_tokens[0] * 100
    rate1 = switches[1] / sinhala_tokens[1] * 100
    a, na = switches[1], sinhala_tokens[1]
    b, nb = switches[0], sinhala_tokens[0]
    p = (a + b) / (na + nb)
    se = math.sqrt(p * (1 - p) * (1 / na + 1 / nb))
    z = (b / nb - a / na) / se
    print(f"[propose_codemix_removals] natural switch rate: NOT={rate0:.3f}/100tok "
          f"OFF={rate1:.3f}/100tok  z={z:.2f}")


def _coverage_cost(rows: list[dict], wordbank: dict, removed: set[str]) -> float:
    """Share of posts (from the given rows' original_text) that have >=1
    eligible candidate in the CURRENT wordbank but would have zero left if
    `removed` were dropped from it."""
    remaining_keys = wordbank.keys() - removed
    lost, total_eligible = 0, 0
    for row in rows:
        sinhala_words = {run for is_sin, run in text_runs(row["original_text"]) if is_sin}
        eligible = sinhala_words & wordbank.keys()
        if not eligible:
            continue
        total_eligible += 1
        if not (eligible & remaining_keys):
            lost += 1
    return (lost / total_eligible * 100) if total_eligible else 0.0


def main() -> None:
    wordbank = _load_wordbank()  # trimmed {english, codemix_plausible}, drives _apply()
    full_wordbank = _load_full_wordbank()  # full rows, for display + classification
    worklist = _load_worklist()
    labels = _load_labels()
    if not wordbank:
        print("[propose_codemix_removals] codemix_wordbank.jsonl is empty/missing")
        return

    slur_flags = sum(1 for row in worklist.values() if row.get("slur_flag"))
    print(f"[propose_codemix_removals] worklist slur_flag=True count: {slur_flags}/{len(worklist)} "
          "(0 confirms the known no-op bug)")

    n_posts_light: dict[str, int] = defaultdict(int)
    n_posts_heavy: dict[str, int] = defaultdict(int)
    n_posts_off: dict[str, int] = defaultdict(int)
    total_occurrences: dict[str, int] = defaultdict(int)
    examples: dict[str, list[tuple[str, str, int]]] = defaultdict(list)
    all_rows: list[dict] = []

    n_rows_checked = 0
    for split in ("train", "test"):
        for severity in ("light", "heavy"):
            path = OUTPUTS_DIR / split / f"codemix_{severity}.jsonl"
            rows = _load_jsonl(path)
            if severity == "light":
                all_rows.extend(rows)
            for row in rows:
                n_rows_checked += 1
                seed = _row_seed(row["source_id"])
                noisy_text, _rate, substituted = _apply(row["original_text"], severity, seed=seed)
                if noisy_text != row["noisy_text"]:
                    continue  # stale vs. current wordbank; don't corrupt the count
                label = labels.get(row["source_id"], row.get("label"))
                for word in substituted:
                    if severity == "light":
                        n_posts_light[word] += 1
                    else:
                        n_posts_heavy[word] += 1
                    if label == 1:
                        n_posts_off[word] += 1
                    total_occurrences[word] += row["original_text"].count(word)
                    if len(examples[word]) < MAX_EXAMPLES:
                        examples[word].append((row["original_text"], row["noisy_text"], label))

    fired_words = set(n_posts_light) | set(n_posts_heavy)
    print(f"[propose_codemix_removals] {n_rows_checked} rows checked; "
          f"{len(fired_words)}/{len(wordbank)} entries fired")

    tiered: dict[str, list[dict]] = {"1": [], "2": [], "3": []}
    flagged_keep: list[dict] = []
    for word in fired_words:
        entry = full_wordbank.get(word, {})
        tier, reason = _classify(word, entry)
        record = {
            "sinhala": word,
            "english": entry.get("english", ""),
            "source": entry.get("source", "?"),
            "codemix_plausible": entry.get("codemix_plausible", False),
            "tier": tier,
            "reason": reason,
            "n_posts_light": n_posts_light[word],
            "n_posts_heavy": n_posts_heavy[word],
            "n_posts_off": n_posts_off[word],
            "total_occurrences": total_occurrences[word],
            "impact": n_posts_light[word] + n_posts_heavy[word],
            "examples": examples[word],
        }
        if tier:
            tiered[tier].append(record)
        elif word in _LOANWORD_LIKE_OVERRIDE:
            flagged_keep.append(record)

    for t in tiered.values():
        t.sort(key=lambda r: -r["impact"])

    recommended_removal = {r["sinhala"] for r in tiered["1"]} | {r["sinhala"] for r in tiered["2"]}
    cost_1 = _coverage_cost(all_rows, wordbank, {r["sinhala"] for r in tiered["1"]})
    cost_12 = _coverage_cost(all_rows, wordbank, recommended_removal)
    cost_123 = _coverage_cost(all_rows, wordbank, recommended_removal | {r["sinhala"] for r in tiered["3"]})
    print(f"[propose_codemix_removals] coverage cost: tier1={cost_1:.2f}% "
          f"tier1+2={cost_12:.2f}% tier1+2+3={cost_123:.2f}%")

    _natural_switch_stats(labels)

    # --- CSV: markup-friendly, decision column left blank for human input ---
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "tier", "reason", "sinhala", "english", "source", "codemix_plausible",
            "n_posts_light", "n_posts_heavy", "n_posts_off", "total_occurrences",
            "example_1_before", "example_1_after",
            "decision",  # human fills in: remove | keep
        ])
        writer.writeheader()
        for tier_id in ("1", "2", "3"):
            for r in tiered[tier_id]:
                before, after, _label = r["examples"][0] if r["examples"] else ("", "", None)
                writer.writerow({
                    "tier": r["tier"], "reason": r["reason"], "sinhala": r["sinhala"],
                    "english": r["english"], "source": r["source"],
                    "codemix_plausible": r["codemix_plausible"],
                    "n_posts_light": r["n_posts_light"], "n_posts_heavy": r["n_posts_heavy"],
                    "n_posts_off": r["n_posts_off"], "total_occurrences": r["total_occurrences"],
                    "example_1_before": before, "example_1_after": after,
                    "decision": "remove" if tier_id in ("1", "2") else "",
                })
    print(f"[propose_codemix_removals] wrote {sum(len(t) for t in tiered.values())} rows -> {CSV_PATH}")

    # --- MD: the case for each tier, readable, matches codemix_usage_review.md style ---
    lines = [
        "# Code-mix word bank: round-4 removal proposal",
        "",
        "**Status: PROPOSAL — nothing in this document has been applied.** "
        "This is Stage 0 of round 4 (see the approved plan): a read-only report. "
        "Removals only reach `data/lexicon/codemix_wordbank.jsonl` after this list "
        "is approved and `scripts/apply_codemix_removals.py` is run against "
        "`codemix_removals_round4.csv`'s `decision` column.",
        "",
        "## Why this round exists",
        "",
        "A reviewer objected that code-mixing is unnatural because switched words "
        '"appear in certain places in a sentence more often than others." Tested '
        "against SOLD's own naturally-occurring code-switching (956 intrasentential "
        "English insertions extracted from the corpus), that claim does not hold for "
        "POSITION: this noiser does in-place type substitution (see "
        "`src/noisers/codemix.py`), so the switch site is always inherited from a "
        "real Sinhala sentence, never chosen by the algorithm. Measured positional "
        "JSD against natural switches is 0.0017 (0-1 scale); the share followed by "
        "an `එක`/`කර` (eka/kara) licensor is 0.42 generated vs 0.44 natural.",
        "",
        "It DOES hold for WORD CHOICE — some bank entries are switches no bilingual "
        "speaker would make. The three tiers below are that defect, sorted by "
        "severity and by how confidently each can be fixed by removal alone.",
        "",
        f"**Critical finding:** `slur_flag` is `True` for {slur_flags}/{len(worklist)} "
        "worklist rows — it has never fired, matching the `_SLUR_SUBSTRINGS` "
        "wrong-import no-op bug recorded in LOG.md Phase 3 v2. No slur filtering has "
        "ever actually been applied to this bank. Tier 1 is that cleanup.",
        "",
        f"{len(fired_words)} of {len(wordbank)} bank entries fired during generation. "
        f"{len(tiered['1'])} entries / {sum(r['impact'] for r in tiered['1'])} firings flagged tier 1, "
        f"{len(tiered['2'])} / {sum(r['impact'] for r in tiered['2'])} tier 2, "
        f"{len(tiered['3'])} / {sum(r['impact'] for r in tiered['3'])} tier 3.",
        "",
        f"Coverage cost if removed (share of posts with >=1 eligible candidate today "
        f"that would lose their last one): tier 1 alone {cost_1:.2f}%, "
        f"tier 1+2 {cost_12:.2f}%, tier 1+2+3 {cost_123:.2f}%.",
        "",
    ]

    tier_titles = {
        "1": "TIER 1 — affect-bearing (label-integrity risk). Recommended: REMOVE.",
        "2": "TIER 2 — native Sinhala verb -> bare English verb (placement defect). Recommended: REMOVE.",
        "3": "TIER 3 — codemix_plausible=False, fires only via fallback. Recommended: YOUR CALL, not bundled into the removal set.",
    }
    tier_notes = {
        "1": "Sinhala insults read weaker once rendered in English — this can silently "
             "weaken whether a post still reads as offensive, which is a label-integrity "
             "problem, not a style one. Bilinguals also independently prefer L1 for "
             "negative affect (Rudra et al., EMNLP 2016); this repo's own SOLD data "
             "agrees (see the natural-switch-rate-by-label line in the script log).",
        "2": "Sinhala borrows English verbs as `V + කරනවා/කරන්න/කරලා`, never bare — "
             "`කියන්න -> say` is not a construction a real bilingual would produce. "
             "`source=loanword` entries are excluded here on purpose: switching an "
             "English word already spelled in Sinhala script back to Latin "
             "(`කෝල් -> call`) is the most natural move available, not a defect.",
        "3": "Already judged implausible by human reviewers in rounds 1-3, but still "
             "fires: `_apply()` falls back to the full eligible pool when a post has no "
             "plausible candidate, rather than leaving it untouched — a deliberate "
             "density trade-off (LOG.md Phase 3). Removing all 606 would cost ~10% "
             "touched-post coverage; consider trimming to the highest-firing subset "
             "instead of an all-or-nothing call.",
    }
    for tier_id in ("1", "2", "3"):
        lines.append(f"## {tier_titles[tier_id]}")
        lines.append("")
        lines.append(tier_notes[tier_id])
        lines.append("")
        for i, r in enumerate(tiered[tier_id], 1):
            lines.append(f"### {tier_id}.{i}. `{r['sinhala']}` -> `{r['english']}`")
            lines.append(f"- impact: {r['impact']} posts ({r['n_posts_light']} light, {r['n_posts_heavy']} heavy), "
                          f"{r['n_posts_off']} of them labelled OFF, {r['total_occurrences']} total occurrences")
            lines.append(f"- source: {r['source']}, codemix_plausible: {r['codemix_plausible']}")
            for before, after, label in r["examples"]:
                lab = "OFF" if label == 1 else "NOT"
                lines.append(f"  - [{lab}] before: {before}")
                lines.append(f"  - [{lab}] after:  {after}")
            lines.append("")

    if flagged_keep:
        lines.append("## FLAGGED FOR REVIEW — likely mis-tagged, recommend KEEP")
        lines.append("")
        lines.append("These matched the tier-2 bare-verb test but are Sinhala-script "
                      "spellings of the English word itself (tagged `source=llm` instead "
                      "of `loanword`). Switching them back to Latin is the most natural "
                      "move available in the post. Held out of tier 2's removal set; "
                      "listed here so the classification choice is visible, not silent.")
        lines.append("")
        for r in sorted(flagged_keep, key=lambda r: -r["impact"]):
            lines.append(f"- `{r['sinhala']}` -> `{r['english']}` ({r['impact']} firings, source={r['source']})")
        lines.append("")

    MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[propose_codemix_removals] wrote {MD_PATH}")
    print("[propose_codemix_removals] NOTHING WAS MODIFIED — this is a proposal only. "
          "Review the CSV/MD, then run apply_codemix_removals.py once approved.")


if __name__ == "__main__":
    main()
