"""
Generate the `transliteration` noised condition for SOLD, both severities,
per split — real Phase 5 output, not a throwaway sample (Phase 2 has no
reason to regenerate this later once it clears its realism target).

Writes data/outputs/{split}/transliteration_{severity}.jsonl, one
schema.Row per SOLD post, validated before being written. The SOLD
train/test split is preserved throughout: train and test are processed
and written completely separately — never merged, never cross-referenced.

--- per-row seed derivation (first-attempt bug, fixed) ---
The first attempt passed the SAME constant seed to apply() for every post.
Since apply() does `random.Random(seed)` fresh each call, every post's word
sequence replayed the IDENTICAL draw sequence from position 0 — so post 1's
first word, post 2's first word, ... all got the same random.random() draw,
and since most SOLD posts are short, the aggregate realised_noise_rate was
dominated by that one fixed sequence's early values rather than reflecting
the true target probability (measured: light landed at 0.096 vs a 0.2
target, heavy at 0.282 vs 0.5 — both far outside the 0.05 tolerance). Still
fully deterministic, just badly correlated across posts. Fixed by deriving
a per-post seed from (base seed, post_id) via a stable hash (NOT Python's
built-in hash() — that's salted per-process via PYTHONHASHSEED and would
break reproducibility across runs).

Run:  python scripts/generate_transliteration.py

Demo mode — quick, ad-hoc, does not touch data/outputs/ or the SOLD
pipeline at all:
  python scripts/generate_transliteration.py --demo data/demo/demo_paragraphs.json
Reads a JSON list of plain text strings and prints original/light/heavy
transliteration for each to stdout.
"""

from __future__ import annotations

import argparse
import json
import sys
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.noisers.transliteration import apply, GENERATOR_VERSION  # noqa: E402
from src.schema import Row  # noqa: E402

SOLD_DIR = REPO_ROOT / "data" / "sold"
OUTPUT_DIR = REPO_ROOT / "data" / "outputs"

SEED = 1337
SEVERITIES = ("light", "heavy")
SPLITS = ("train", "test")


def log(msg: str) -> None:
    print(f"[generate_transliteration] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _row_seed(post_id: str) -> int:
    """Deterministic per-row seed from (SEED, post_id) — stable across
    processes/runs (unlike Python's built-in hash())."""
    return zlib.crc32(f"{SEED}:{post_id}".encode("utf-8"))


def generate_split_severity(split: str, severity: str, rows: list[dict]) -> dict:
    out_dir = OUTPUT_DIR / split
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"transliteration_{severity}.jsonl"

    rates = []
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            noisy_text, realised_rate = apply(row["text"], severity, seed=_row_seed(row["post_id"]))
            out_row = Row(
                source_id=row["post_id"],
                split=split,
                condition="transliteration",
                severity=severity,
                original_text=row["text"],
                noisy_text=noisy_text,
                label=row["label"],
                realised_noise_rate=realised_rate,
                generator_version=GENERATOR_VERSION,
            )
            out_row.validate()
            f.write(json.dumps(out_row.to_dict(), ensure_ascii=False) + "\n")
            rates.append(realised_rate)

    avg_rate = sum(rates) / len(rates) if rates else 0.0
    log(f"{split}/{severity}: {len(rows)} rows -> {out_path} (mean realised_noise_rate={avg_rate:.3f})")
    return {"n_rows": len(rows), "mean_realised_noise_rate": avg_rate}


def run_demo(path: Path) -> None:
    """Quick, ad-hoc demo: read a JSON list of plain text strings, print
    original/light/heavy transliteration for each. Does not touch
    data/outputs/ or the SOLD pipeline."""
    parts = json.loads(path.read_text(encoding="utf-8"))
    for i, text in enumerate(parts):
        seed = zlib.crc32(f"{SEED}:demo:{i}".encode("utf-8"))
        light, rate_l = apply(text, "light", seed=seed)
        heavy, rate_h = apply(text, "heavy", seed=seed)
        print(f"--- part {i} ---")
        print("ORIGINAL:", text)
        print(f"LIGHT (rate={rate_l:.2f}):", light)
        print(f"HEAVY (rate={rate_h:.2f}):", heavy)
        print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--demo", type=Path, default=None,
        help="path to a JSON list of plain text strings; runs a quick ad-hoc "
             "demo instead of the real SOLD generation pipeline",
    )
    args = parser.parse_args()

    if args.demo is not None:
        run_demo(args.demo)
        return

    summary = {}
    for split in SPLITS:
        rows = _load_jsonl(SOLD_DIR / f"{split}.jsonl")
        for severity in SEVERITIES:
            summary[f"{split}/{severity}"] = generate_split_severity(split, severity, rows)
    log("done.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
