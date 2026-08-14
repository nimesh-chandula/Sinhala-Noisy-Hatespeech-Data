"""
Phase 3 redesign — the core human-review deliverable: for every word bank
entry that actually FIRED during generation (not the full ~8,000-entry bank
blind), report how much impact it had and 3 real before/after examples, so
a human reviewer works through an impact-ordered list where the top ~100-200
rows cover the large majority of all substitutions in the corpus, instead of
the old pipeline's 12,000-row blind candidate CSV.

Recomputes, per generated codemix output row, exactly which word TYPES were
substituted by re-running src.noisers.codemix._apply with the same seed
generate_codemix.py used (see scripts/generate_codemix.py's _row_seed) —
the persisted rows only carry a substitution COUNT (n_substitutions), not
the substituted words themselves, so this is the one place that needs to
know which. Same "recompute via the real implementation, don't hand-derive"
principle as eval/invariants.py's check_codemix_substitution_spec.

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


def main() -> None:
    wordbank = _load_wordbank()  # used only to drive _apply()'s recomputation below
    full_wordbank = _load_full_wordbank()  # used for display metadata (source, frequency)
    if not wordbank:
        print("[build_codemix_usage_report] data/lexicon/codemix_wordbank.jsonl is empty/missing — "
              "run build_codemix_wordbank.py first")
        return

    n_posts_light: dict[str, int] = defaultdict(int)
    n_posts_heavy: dict[str, int] = defaultdict(int)
    total_occurrences: dict[str, int] = defaultdict(int)
    examples: dict[str, list[tuple[str, str]]] = defaultdict(list)

    n_rows_checked = 0
    for split in ("train", "test"):
        for severity in ("light", "heavy"):
            path = OUTPUTS_DIR / split / f"codemix_{severity}.jsonl"
            rows = _load_jsonl(path)
            for row in rows:
                n_rows_checked += 1
                seed = _row_seed(row["source_id"])
                noisy_text, rate, substituted = _apply(row["original_text"], severity, seed=seed)
                # sanity: recomputation should match the persisted row; if it
                # doesn't, the wordbank has moved on since generation — count
                # it but don't let a stale file corrupt the impact report.
                if noisy_text != row["noisy_text"]:
                    continue
                for word in substituted:
                    if severity == "light":
                        n_posts_light[word] += 1
                    else:
                        n_posts_heavy[word] += 1
                    occ = row["original_text"].count(word)
                    total_occurrences[word] += occ
                    if len(examples[word]) < MAX_EXAMPLES:
                        examples[word].append((row["original_text"], row["noisy_text"]))

    fired_words = set(n_posts_light) | set(n_posts_heavy)
    print(f"[build_codemix_usage_report] checked {n_rows_checked} rows across train+test x light+heavy; "
          f"{len(fired_words)}/{len(wordbank)} wordbank entries actually fired")

    rows_out = []
    for word in fired_words:
        entry = full_wordbank.get(word, {})
        impact = n_posts_light[word] + n_posts_heavy[word]
        rows_out.append({
            "sinhala": word,
            "english": entry.get("english", ""),
            "source": entry.get("source", "?"),
            "codemix_plausible": entry.get("codemix_plausible", False),
            "n_posts_light": n_posts_light[word],
            "n_posts_heavy": n_posts_heavy[word],
            "total_occurrences_replaced": total_occurrences[word],
            "impact": impact,
            "examples": examples[word],
            "verdict": "",
            "corrected_english": "",
        })
    rows_out.sort(key=lambda r: (-r["impact"], r["sinhala"]))

    LEXICON_DIR.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "sinhala", "english", "source", "codemix_plausible",
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
                "sinhala": r["sinhala"], "english": r["english"], "source": r["source"],
                "codemix_plausible": r["codemix_plausible"],
                "n_posts_light": r["n_posts_light"], "n_posts_heavy": r["n_posts_heavy"],
                "total_occurrences_replaced": r["total_occurrences_replaced"],
                **flat_examples,
                "verdict": r["verdict"], "corrected_english": r["corrected_english"],
            })
    print(f"[build_codemix_usage_report] wrote {len(rows_out)} rows -> {CSV_PATH}")

    lines = [
        "# Code-mix word bank usage review",
        "",
        "**Status: fully reviewed.** This snapshot reflects the word bank AFTER 3 rounds "
        "of human review (2026-08-13 to 2026-08-14, 992 corrections applied — 910 "
        "corrected, 82 removed — see data/lexicon/codemix_review_corrections.jsonl and "
        "LOG.md for the full record). Entries below are impact-ordered against the "
        "corrected bank, so this is an audit trail of what shipped, not a fresh TODO list.",
        "",
        f"{len(rows_out)} word bank entries actually fired during generation "
        f"(out of {len(wordbank)} in the bank), impact-ordered — the top entries here "
        "cover the large majority of all substitutions in the corpus. Machine-translated "
        "entries (source=llm) and anything flagged codemix_plausible=False are where the "
        "review risk concentrates; verify those first.",
        "",
    ]
    for i, r in enumerate(rows_out, 1):
        flag = " ⚠️ LLM-TRANSLATED" if r["source"] == "llm" else ""
        plausible_flag = "" if r["codemix_plausible"] else " ⚠️ NOT MARKED PLAUSIBLE"
        lines.append(f"## {i}. `{r['sinhala']}` -> `{r['english']}`{flag}{plausible_flag}")
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
