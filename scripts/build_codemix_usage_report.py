"""
Phase 3 redesign — the core human-review deliverable: for every word bank
entry that actually FIRED during generation (not the full ~8,000-entry bank
blind), report how much impact it had and 3 real before/after examples, so
a human reviewer works through an impact-ordered list where the top ~100-200
rows cover the large majority of all substitutions in the corpus, instead of
the old pipeline's 12,000-row blind candidate CSV.

Recomputes, per generated codemix output row, exactly which UNITS (single
words AND round-5 phrase-bank spans) were substituted by re-running
src.noisers.codemix._apply with the same seed generate_codemix.py used (see
scripts/generate_codemix.py's _row_seed) — the persisted rows only carry a
substitution COUNT (n_substitutions), not the substituted content itself,
so this is the one place that needs to know which. Same "recompute via the
real implementation, don't hand-derive" principle as eval/invariants.py's
check_codemix_substitution_spec.

Round 5: reports word-bank and phrase-bank entries together in one
impact-ordered list (a `kind` column distinguishes them), since both are
now real substitutable sources a reviewer needs to see ranked by impact,
not just the word bank.

Writes:
  data/lexicon/codemix_usage_review.csv  (for marking up: verdict, corrected_english)
  data/lexicon/codemix_usage_review.md   (for reading)

Run:  python scripts/build_codemix_usage_report.py
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src.noisers.codemix import _apply, _load_wordbank  # noqa: E402
from generate_codemix import _row_seed  # noqa: E402

OUTPUTS_DIR = REPO_ROOT / "data" / "outputs"
LEXICON_DIR = REPO_ROOT / "data" / "lexicon"
WORDBANK_PATH = LEXICON_DIR / "codemix_wordbank.jsonl"
PHRASEBANK_PATH = LEXICON_DIR / "codemix_phrasebank.jsonl"
CSV_PATH = LEXICON_DIR / "codemix_usage_review.csv"
MD_PATH = LEXICON_DIR / "codemix_usage_review.md"
MAX_EXAMPLES = 3


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_full_wordbank() -> dict[str, dict]:
    """Full rows (sinhala, english, source, codemix_plausible, sold_frequency,
    evidence), keyed by sinhala — unlike src.noisers.codemix._load_wordbank(),
    which is deliberately trimmed to just {english, codemix_plausible} for
    the noiser's own runtime use and doesn't carry `source`, which this
    report needs to flag machine-translated entries for review."""
    return {row["sinhala"]: row for row in _load_jsonl(WORDBANK_PATH)}


def _load_full_phrasebank() -> dict[str, dict]:
    """Same idea as _load_full_wordbank(), for the round-5 phrase bank."""
    return {row["sinhala"]: row for row in _load_jsonl(PHRASEBANK_PATH)}


def main() -> None:
    wordbank = _load_wordbank()  # used only to drive _apply()'s recomputation below
    full_wordbank = _load_full_wordbank()  # used for display metadata (source, frequency)
    full_phrasebank = _load_full_phrasebank()
    if not wordbank:
        print("[build_codemix_usage_report] data/lexicon/codemix_wordbank.jsonl is empty/missing — "
              "run build_codemix_wordbank.py first")
        return

    n_posts_light: dict[tuple[str, str], int] = defaultdict(int)
    n_posts_heavy: dict[tuple[str, str], int] = defaultdict(int)
    total_occurrences: dict[tuple[str, str], int] = defaultdict(int)
    examples: dict[tuple[str, str], list[tuple[str, str]]] = defaultdict(list)

    n_rows_checked = 0
    for split in ("train", "test"):
        for severity in ("light", "heavy"):
            path = OUTPUTS_DIR / split / f"codemix_{severity}.jsonl"
            rows = _load_jsonl(path)
            for row in rows:
                n_rows_checked += 1
                seed = _row_seed(row["source_id"])
                noisy_text, rate, chosen_units, target_cmi = _apply(row["original_text"], severity, seed=seed)
                # sanity: recomputation should match the persisted row; if it
                # doesn't, a frozen file has moved on since generation — count
                # it but don't let a stale file corrupt the impact report.
                if noisy_text != row["noisy_text"]:
                    continue
                for unit in chosen_units:
                    if unit["entry"] is None:
                        key = ("word", unit["text"])
                    else:
                        key = ("phrase", unit["entry"]["sinhala"])
                    if severity == "light":
                        n_posts_light[key] += 1
                    else:
                        n_posts_heavy[key] += 1
                    sinhala_form = key[1]
                    occ = row["original_text"].count(sinhala_form)
                    total_occurrences[key] += occ
                    if len(examples[key]) < MAX_EXAMPLES:
                        examples[key].append((row["original_text"], row["noisy_text"]))

    fired_keys = set(n_posts_light) | set(n_posts_heavy)
    n_fired_words = sum(1 for kind, _ in fired_keys if kind == "word")
    n_fired_phrases = sum(1 for kind, _ in fired_keys if kind == "phrase")
    print(f"[build_codemix_usage_report] checked {n_rows_checked} rows across train+test x light+heavy; "
          f"{n_fired_words}/{len(wordbank)} wordbank entries + {n_fired_phrases} phrasebank entries actually fired")

    rows_out = []
    for key in fired_keys:
        kind, sinhala_form = key
        if kind == "word":
            entry = full_wordbank.get(sinhala_form, {})
            english = entry.get("english", "")
            source = entry.get("source", "?")
            plausible = entry.get("codemix_plausible", False)
        else:
            entry = full_phrasebank.get(sinhala_form, {})
            english = entry.get("english", "")
            source = entry.get("source", "?")
            plausible = entry.get("codemix_plausible", False)
        impact = n_posts_light[key] + n_posts_heavy[key]
        rows_out.append({
            "kind": kind,
            "sinhala": sinhala_form,
            "english": english,
            "source": source,
            "codemix_plausible": plausible,
            "n_posts_light": n_posts_light[key],
            "n_posts_heavy": n_posts_heavy[key],
            "total_occurrences_replaced": total_occurrences[key],
            "impact": impact,
            "examples": examples[key],
            "verdict": "",
            "corrected_english": "",
        })
    rows_out.sort(key=lambda r: (-r["impact"], r["sinhala"]))

    LEXICON_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "kind", "sinhala", "english", "source", "codemix_plausible",
            "n_posts_light", "n_posts_heavy", "total_occurrences_replaced",
            "example_1_before", "example_1_after",
            "example_2_before", "example_2_after",
            "example_3_before", "example_3_after",
            "verdict", "corrected_english",
        ])
        writer.writeheader()
        for r in rows_out:
            flat_examples = {}
            for i in range(MAX_EXAMPLES):
                before, after = r["examples"][i] if i < len(r["examples"]) else ("", "")
                flat_examples[f"example_{i + 1}_before"] = before
                flat_examples[f"example_{i + 1}_after"] = after
            writer.writerow({
                "kind": r["kind"], "sinhala": r["sinhala"], "english": r["english"], "source": r["source"],
                "codemix_plausible": r["codemix_plausible"],
                "n_posts_light": r["n_posts_light"], "n_posts_heavy": r["n_posts_heavy"],
                "total_occurrences_replaced": r["total_occurrences_replaced"],
                **flat_examples,
                "verdict": r["verdict"], "corrected_english": r["corrected_english"],
            })
    print(f"[build_codemix_usage_report] wrote {len(rows_out)} rows -> {CSV_PATH}")

    lines = [
        "# Code-mix word + phrase bank usage review",
        "",
        "**Status: round 5.** This snapshot reflects the word bank AFTER 4 rounds "
        "of human review (rounds 1-3: 2026-08-13 to 2026-08-14, 992 corrections — 910 "
        "corrected, 82 removed; round 4: 2026-08-18, 97 further removals — 30 "
        "affect-bearing, 67 bare-verb, evidence-based via "
        "data/lexicon/codemix_removals_round4.md, plus an attestation-aware selection "
        "redesign, see data/lexicon/codemix_selection_comparison.md), PLUS round 5's new "
        "phrase bank (data/lexicon/codemix_phrasebank.jsonl, 1,160 plausible 2-3 word "
        "spans out of 8,682 mined and translated — see docs/research_documentation.md "
        "§9.11). Entries below are impact-ordered, word and phrase entries together (the "
        "`kind` column distinguishes them), so this is an audit trail of what shipped, "
        "not a fresh TODO list. Previous word-only snapshot archived at "
        "codemix_usage_review_round3.md.",
        "",
        f"{len(rows_out)} entries actually fired during generation "
        f"({n_fired_words}/{len(wordbank)} word bank, {n_fired_phrases} phrase bank), "
        "impact-ordered — the top entries here cover the large majority of all "
        "substitutions in the corpus. Machine-translated entries (source=llm) and "
        "anything flagged codemix_plausible=False are where the review risk "
        "concentrates; verify those first.",
        "",
    ]
    for i, r in enumerate(rows_out, 1):
        kind_flag = f" [{r['kind'].upper()}]"
        flag = " ⚠️ LLM-TRANSLATED" if r["source"] == "llm" else ""
        plausible_flag = "" if r["codemix_plausible"] else " ⚠️ NOT MARKED PLAUSIBLE"
        lines.append(f"## {i}.{kind_flag} `{r['sinhala']}` -> `{r['english']}`{flag}{plausible_flag}")
        lines.append(f"- impact: {r['impact']} posts ({r['n_posts_light']} light, {r['n_posts_heavy']} heavy), "
                      f"{r['total_occurrences_replaced']} total occurrences replaced")
        lines.append(f"- source: {r['source']}")
        for before, after in r["examples"]:
            lines.append(f"  - before: {before}")
            lines.append(f"  - after:  {after}")
        lines.append("")
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"[build_codemix_usage_report] wrote readable version -> {MD_PATH}")


if __name__ == "__main__":
    main()
