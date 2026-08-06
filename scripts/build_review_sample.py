"""
Build a human-review sample: 100 transliteration items to manually judge
"would a real person type this?" against, as a text-quality checkpoint
before the next noise vector (code-mixing) is built.

Deterministically drawn from the TRAIN split only (consistent with the
train-only convention used for the LoRA sample later — this is purely a
text-quality review, not a training-data decision, but staying train-only
avoids any future ambiguity about touching test data before it's needed).

50 items at "light" severity + 50 at "heavy", seed 1337.

Writes:
  data/outputs/human_review_sample.jsonl  (raw rows, for programmatic use)
  data/outputs/human_review_sample.md     (Sinhala original next to noisy
                                            text, for easy human reading)

Run:  python scripts/build_review_sample.py
"""

from __future__ import annotations

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


def main() -> None:
    rng = random.Random(SEED)
    sample: list[dict] = []
    for severity in ("light", "heavy"):
        rows = _load_jsonl(OUTPUTS_DIR / "train" / f"transliteration_{severity}.jsonl")
        sample.extend(rng.sample(rows, N_PER_SEVERITY))

    jsonl_path = OUTPUTS_DIR / "human_review_sample.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for row in sample:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    md_path = OUTPUTS_DIR / "human_review_sample.md"
    lines = [
        "# Transliteration human review sample",
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


if __name__ == "__main__":
    main()
