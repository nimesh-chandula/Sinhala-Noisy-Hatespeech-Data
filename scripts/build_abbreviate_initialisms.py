"""
Phase 4b, Stage 1b -- derive Channel B of the abbreviation noiser: PHRASE-level
initialism (a multi-word phrase collapses to first-letters, e.g. a two-word
phrase -> "X. Y."), as opposed to Channel A's single-word clipping (see
scripts/build_abbreviate_clippings.py).

--- Why this channel exists ---
You flagged a real pattern the word-clipping mechanism can't produce: casual
Sinhala texting abbreviates offensive multi-word phrases to their initials
(e.g. a two-word slur phrase -> its first letters). Since this pipeline's
whole purpose is benchmarking a hate-speech classifier under realistic noise
(CLAUDE.md's mission), an evasively-abbreviated slur is exactly the kind of
noise such a classifier needs to be tested against -- SOLD's own labels are
preserved untouched (schema.Row.label is inherited from source, never
recomputed), so this transforms already-labeled text, it doesn't invent new
offensive content.

--- Corpus-grounded candidate surfacing, not hand-listing ---
Rather than me hand-listing slurs, candidate bigrams are mined purely from
SOLD's own adjacency and label statistics: every pair of Sinhala words that
appear back-to-back (separated by nothing but whitespace) somewhere in SOLD,
above a frequency floor, ranked by frequency with each one's OFF-label
association rate computed alongside it (fraction of its occurrences sitting
in an OFF-labeled post). Measured once during planning: 563 bigrams
(freq>=8) exist overall; 62 of those are >85% OFF-associated -- a real,
corpus-grounded signal for "this pair co-occurs almost exclusively in
offensive posts," surfaced for review, not filtered to ONLY that case (the
mechanism is general -- any sufficiently common phrase is a candidate,
offensive phrases are simply where this matters most for the downstream
task).

--- Opt-IN, not opt-out (deliberately different from Channel A) ---
Channel A's clippings default to "accept unless a human rejects it" --
reasonable for ordinary vocabulary. Channel B is different: because a
meaningful fraction of high-ranking candidates will be offensive-phrase
material, NOTHING ships in the frozen lexicon unless a human EXPLICITLY
approves that exact bigram (an "approve_bigram" correction). An unreviewed
or rejected candidate is simply absent, not merely deprioritized. This is a
more conservative default than every other lexicon in this repo, chosen
because this is the one mechanism in the whole project whose highest-value
use case is modeling evasive obscenity.

--- The abbreviated form itself ---
NOT stored here -- it's generated mechanically at generation time from the
frozen (word1, word2) pair: first grapheme cluster of each word, joined as
"{c1}. {c2}." (src/noisers/abbreviate.py implements this). Only WHICH
bigrams are eligible is a review decision; the transform itself is a fixed
rule once a bigram is approved, so there's no separate "propose the
abbreviated spelling" step the way codemix needed for translations.

Writes:
  data/lexicon/abbreviate_initialisms.jsonl        frozen (APPROVED bigrams only)
  data/lexicon/.abbreviate_initialisms.sha256       hash, stamped into GENERATOR_VERSION
  data/lexicon/abbreviate_initialisms_candidates.csv   for marking up approvals
  data/lexicon/abbreviate_initialisms_candidates.md    for reading

Run:  python scripts/build_abbreviate_initialisms.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402
from src.noisers.abbreviate import initials  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
SOLD_DIR = DATA_DIR / "sold"
LEXICON_DIR = DATA_DIR / "lexicon"

INITIALISMS_PATH = LEXICON_DIR / "abbreviate_initialisms.jsonl"
INITIALISMS_HASH_PATH = LEXICON_DIR / ".abbreviate_initialisms.sha256"
CORRECTIONS_PATH = LEXICON_DIR / "abbreviate_review_corrections.jsonl"
CANDIDATES_CSV_PATH = LEXICON_DIR / "abbreviate_initialisms_candidates.csv"
CANDIDATES_MD_PATH = LEXICON_DIR / "abbreviate_initialisms_candidates.md"

FREQ_FLOOR = 8
MAX_EXAMPLES = 3


def log(msg: str) -> None:
    print(f"[build_abbreviate_initialisms] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def mine_bigrams() -> tuple[dict[tuple[str, str], int], dict[tuple[str, str], int], dict[tuple[str, str], list[str]]]:
    """(total_freq, off_freq, examples) for every Sinhala word bigram that
    occurs back-to-back (whitespace-only between them, no other punctuation)
    somewhere in SOLD train+test."""
    total: dict[tuple[str, str], int] = defaultdict(int)
    off: dict[tuple[str, str], int] = defaultdict(int)
    examples: dict[tuple[str, str], list[str]] = defaultdict(list)

    for split in ("train", "test"):
        with (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                row = json.loads(line)
                text = row["text"]
                is_off = row["label"] == 1
                runs = text_runs(text)
                seen_this_post: set[tuple[str, str]] = set()
                for i in range(len(runs) - 2):
                    is_sin_a, a = runs[i]
                    is_connector, connector = runs[i + 1]
                    is_sin_b, b = runs[i + 2]
                    if not (is_sin_a and is_sin_b):
                        continue
                    if is_connector or connector.strip() != "":
                        continue  # not whitespace-only between them
                    bg = (a, b)
                    total[bg] += 1
                    if is_off:
                        off[bg] += 1
                    if bg not in seen_this_post:
                        seen_this_post.add(bg)
                        if len(examples[bg]) < MAX_EXAMPLES:
                            examples[bg].append(text)

    return dict(total), dict(off), dict(examples)


def merge_approvals(
    total: dict[tuple[str, str], int]
) -> tuple[dict[tuple[str, str], dict], int]:
    """Opt-in merge: a bigram enters the frozen lexicon ONLY via an explicit
    {"action": "approve_bigram", "word1": ..., "word2": ...} correction.
    "reject_bigram" corrections are accepted too (so a reviewer can record an
    explicit no, not just silence) but have no additional effect beyond not
    approving -- absence already means excluded."""
    approved: dict[tuple[str, str], dict] = {}
    n_approved = 0
    for row in _load_jsonl(CORRECTIONS_PATH):
        action = row["action"]
        if action not in ("approve_bigram", "reject_bigram"):
            continue  # other actions belong to build_abbreviate_clippings.py
        key = (row["word1"], row["word2"])
        if action == "approve_bigram":
            if key not in total:
                log(f"WARNING: approved bigram {key!r} not found in mined candidates -- skipped")
                continue
            approved[key] = {"word1": key[0], "word2": key[1]}
            n_approved += 1
        elif action == "reject_bigram":
            approved.pop(key, None)
    return approved, n_approved


def main() -> None:
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)

    total, off, examples = mine_bigrams()
    candidates = {bg: f for bg, f in total.items() if f >= FREQ_FLOOR}
    log(f"mined {len(total)} distinct back-to-back Sinhala bigrams; "
        f"{len(candidates)} clear freq>={FREQ_FLOOR}")

    off_skewed = [bg for bg in candidates if off.get(bg, 0) / candidates[bg] > 0.85]
    log(f"{len(off_skewed)} candidates are >85% OFF-label associated")

    approved, n_approved = merge_approvals(total)
    corrections = _load_jsonl(CORRECTIONS_PATH)
    n_bigram_corrections = sum(1 for r in corrections if r["action"] in ("approve_bigram", "reject_bigram"))
    if n_bigram_corrections:
        log(f"{n_bigram_corrections} bigram review corrections found -> {n_approved} bigrams approved")
    else:
        log("no review corrections yet -- frozen lexicon is empty until a human approves >=1 bigram")

    # --- write frozen artifact (opt-in: only approved bigrams) ---
    rows_out = sorted(approved.values(), key=lambda r: (r["word1"], r["word2"]))
    with INITIALISMS_PATH.open("w", encoding="utf-8") as f:
        for row in rows_out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(INITIALISMS_PATH.read_bytes()).hexdigest()
    INITIALISMS_HASH_PATH.write_text(digest, encoding="utf-8")
    log(f"wrote {len(rows_out)} APPROVED bigrams -> {INITIALISMS_PATH}")
    log(f"sha256={digest} (first 8: {digest[:8]}) -> {INITIALISMS_HASH_PATH}")

    # --- write candidate review artifacts, impact-ordered ---
    ordered = sorted(candidates, key=lambda bg: -candidates[bg])
    with CANDIDATES_CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "word1", "word2", "freq", "off_rate", "initials_preview",
            "example_1", "example_2", "example_3", "approve", "notes",
        ])
        writer.writeheader()
        for bg in ordered:
            w1, w2 = bg
            exs = examples.get(bg, [])
            writer.writerow({
                "word1": w1, "word2": w2, "freq": candidates[bg],
                "off_rate": round(off.get(bg, 0) / candidates[bg], 3),
                "initials_preview": initials(w1, w2),
                "example_1": exs[0] if len(exs) > 0 else "",
                "example_2": exs[1] if len(exs) > 1 else "",
                "example_3": exs[2] if len(exs) > 2 else "",
                "approve": "yes" if bg in approved else "",
                "notes": "",
            })
    log(f"wrote candidates CSV -> {CANDIDATES_CSV_PATH}")

    lines = [
        "# Abbreviation Channel B (phrase initialism) candidates",
        "",
        f"{len(ordered)} candidate bigrams (freq>={FREQ_FLOOR}), impact-ordered by "
        "frequency. **Opt-in**: NOTHING here ships unless you explicitly approve it -- "
        "see the module docstring in scripts/build_abbreviate_initialisms.py for why. "
        f"Currently {len(approved)}/{len(ordered)} approved.",
        "",
        "To approve a bigram, add a line to "
        "data/lexicon/abbreviate_review_corrections.jsonl: "
        "{\"action\": \"approve_bigram\", \"word1\": ..., \"word2\": ...}. "
        "off_rate is the fraction of this bigram's occurrences that sit in an "
        "OFF-labeled post -- a high off_rate is exactly the case you asked this "
        "channel to cover, but every candidate (any bigram, not just offensive ones) "
        "is listed since the mechanism itself is general.",
        "",
    ]
    for i, bg in enumerate(ordered, 1):
        w1, w2 = bg
        off_rate = off.get(bg, 0) / candidates[bg]
        flag = " ⚠️ HIGH OFF-ASSOCIATION" if off_rate > 0.85 else ""
        approved_flag = " ✅ APPROVED" if bg in approved else ""
        lines.append(f"## {i}. `{w1}` `{w2}` -> `{initials(w1, w2)}` "
                      f"(freq={candidates[bg]}, off_rate={off_rate:.2f}){flag}{approved_flag}")
        for ex in examples.get(bg, []):
            lines.append(f"  - {ex}")
        lines.append("")
    CANDIDATES_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote candidates MD -> {CANDIDATES_MD_PATH}")


if __name__ == "__main__":
    main()
