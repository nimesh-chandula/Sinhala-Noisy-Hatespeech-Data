"""
Build a human-review sample for a given condition: 100 items to manually
judge "would a real person type this?" against, as a text-quality
checkpoint before the next noise vector is built.

Deterministically drawn from the TRAIN split only (consistent with the
train-only convention used for the LoRA sample later — this is purely a
text-quality review, not a training-data decision, but staying train-only
avoids any future ambiguity about touching test data before it's needed).

50 items at "light" severity + 50 at "heavy", seed 1337.

Writes, per condition:
  data/outputs/human_review_sample_{condition}.jsonl  (raw rows)
  data/outputs/human_review_sample_{condition}.md     (Sinhala original
                                            next to noisy text, for reading)

Run:  python scripts/build_review_sample.py --condition transliteration
      python scripts/build_review_sample.py --condition codemix
      python scripts/build_review_sample.py --condition codemix --only-changed

(The original transliteration sample predates the --condition flag and is
kept at its original path, data/outputs/human_review_sample.{jsonl,md},
for continuity with GATE A's already-reviewed sample — see LOG.md.)

--only-changed restricts the draw to rows where noisy_text != original_text
(added for codemix v2's forced-selection redesign — see the plan / LOG.md).
Without it, a condition where most rows are untouched draws a sample that's
mostly unchanged text and reviews nothing; codemix v1 was ~86% untouched, so
this flag existed as an unmet need well before v2 made it worth adding.
Deliberately defined as a straight text comparison rather than reading
n_substitutions or realised_noise_rate — it then works unchanged for every
condition (transliteration, misspell, abbreviate, ...) regardless of
whether that noiser populates n_substitutions at all.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUTPUTS_DIR = REPO_ROOT / "data" / "outputs"
SEED = 1337
N_PER_SEVERITY = 50


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_sample(condition: str, only_changed: bool = False) -> list[dict]:
    rng = random.Random(SEED)
    sample: list[dict] = []
    for severity in ("light", "heavy"):
        rows = _load_jsonl(OUTPUTS_DIR / "train" / f"{condition}_{severity}.jsonl")
        pool = [r for r in rows if r["noisy_text"] != r["original_text"]] if only_changed else rows
        if only_changed and len(pool) < N_PER_SEVERITY:
            print(f"[build_review_sample] WARNING: only {len(pool)} changed rows available "
                  f"for {condition}/{severity} (< {N_PER_SEVERITY} requested) — sampling all of them")
        n = min(N_PER_SEVERITY, len(pool))
        sample.extend(rng.sample(pool, n))
    return sample


def write_sample(condition: str, sample: list[dict], jsonl_path: Path, md_path: Path) -> None:
    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in sample:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        f"# {condition.capitalize()} human review sample",
        "",
        "100 items (50 light + 50 heavy severity), drawn from SOLD train only, seed 1337.",
        "For each: does the noisy text read like something a real person would type?",
        "",
    ]
    for i, row in enumerate(sample, 1):
        lines.append(f"## {i}. `{row['source_id']}` — severity={row['severity']}, "
                      f"label={'OFF' if row['label'] else 'NOT'}, "
                      f"realised_noise_rate={row['realised_noise_rate']:.2f}")
        lines.append(f"- **original**: {row['original_text']}")
        lines.append(f"- **noisy**: {row['noisy_text']}")
        lines.append("")

    md_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[build_review_sample] wrote {len(sample)} items -> {jsonl_path}")
    print(f"[build_review_sample] wrote readable version -> {md_path}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--condition", default="transliteration",
        help="condition to sample (must have data/outputs/train/{condition}_{light,heavy}.jsonl)",
    )
    parser.add_argument(
        "--only-changed", action="store_true",
        help="restrict the draw to rows where noisy_text != original_text",
    )
    args = parser.parse_args()

    sample = build_sample(args.condition, only_changed=args.only_changed)
    if args.condition == "transliteration" and not args.only_changed:
        # original GATE A paths, kept stable for continuity with the
        # already-reviewed sample referenced throughout LOG.md
        jsonl_path = OUTPUTS_DIR / "human_review_sample.jsonl"
        md_path = OUTPUTS_DIR / "human_review_sample.md"
    else:
        suffix = "_changed_only" if args.only_changed else ""
        jsonl_path = OUTPUTS_DIR / f"human_review_sample_{args.condition}{suffix}.jsonl"
        md_path = OUTPUTS_DIR / f"human_review_sample_{args.condition}{suffix}.md"
    write_sample(args.condition, sample, jsonl_path, md_path)


if __name__ == "__main__":
    main()
