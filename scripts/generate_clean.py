"""
Generate the `clean` condition for SOLD, per split — the unmodified source
text wrapped in the standard Row schema, so downstream tooling (the LoRA
sampler, a benchmark harness) can treat "clean" as just another condition
rather than a special case.

Trivial by design: noisy_text == original_text, realised_noise_rate == 0.0,
severity == "none" (the only condition that uses it — see schema.py's
SEVERITIES comment), one file per split (no light/heavy split, since there's
only one variant).

Writes data/outputs/{split}/clean.jsonl, one schema.Row per SOLD post.

Run:  python scripts/generate_clean.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.schema import Row  # noqa: E402

SOLD_DIR = REPO_ROOT / "data" / "sold"
OUTPUT_DIR = REPO_ROOT / "data" / "outputs"

GENERATOR_VERSION = "clean-v1"
SPLITS = ("train", "test")


def log(msg: str) -> None:
    print(f"[generate_clean] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def generate_split(split: str, rows: list[dict]) -> None:
    out_dir = OUTPUT_DIR / split
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "clean.jsonl"

    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            out_row = Row(
                source_id=row["post_id"],
                split=split,
                condition="clean",
                severity="none",
                original_text=row["text"],
                noisy_text=row["text"],
                label=row["label"],
                realised_noise_rate=0.0,
                generator_version=GENERATOR_VERSION,
            )
            out_row.validate()
            f.write(json.dumps(out_row.to_dict(), ensure_ascii=False) + "\n")

    log(f"{split}: {len(rows)} rows -> {out_path}")


def main() -> None:
    for split in SPLITS:
        rows = _load_jsonl(SOLD_DIR / f"{split}.jsonl")
        generate_split(split, rows)
    log("done.")


if __name__ == "__main__":
    main()
