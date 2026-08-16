"""
Generate the `codemix` noised condition for SOLD, both severities, per
split — real Phase 5 output, not a throwaway sample. Near-identical
structure to scripts/generate_transliteration.py (same per-row seeding,
same Row/validate/write path, same output naming convention the harness
globs for) — see that script's docstring for why each piece is built the
way it is; this one only documents what's specific to codemix.

Writes data/outputs/{split}/codemix_{severity}.jsonl, one schema.Row per
SOLD post, validated before being written. The SOLD train/test split is
preserved throughout: train and test are processed and written completely
separately — never merged, never cross-referenced.

Run:  python scripts/generate_codemix.py

Demo mode — quick, ad-hoc, does not touch data/outputs/ or the SOLD
pipeline at all:
  python scripts/generate_codemix.py --demo data/demo/demo_paragraphs.json
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

from src.noisers.codemix import apply, _apply, GENERATOR_VERSION  # noqa: E402
from src.schema import Row  # noqa: E402

SOLD_DIR = REPO_ROOT / "data" / "sold"
OUTPUT_DIR = REPO_ROOT / "data" / "outputs"

SEED = 1337
SEVERITIES = ("light", "heavy")
SPLITS = ("train", "test")


def log(msg: str) -> None:
    print(f"[generate_codemix] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _row_seed(post_id: str) -> int:
    """Deterministic per-row seed from (SEED, post_id) — stable across
    processes/runs (unlike Python's built-in hash()). Same derivation as
    generate_transliteration.py; reusing the same numeric seed value across
    different noiser modules is safe, since each apply() call consumes its
    own independent random.Random(seed) instance."""
    return zlib.crc32(f"{SEED}:{post_id}".encode("utf-8"))


def generate_split_severity(split: str, severity: str, rows: list[dict]) -> dict:
    out_dir = OUTPUT_DIR / split
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"codemix_{severity}.jsonl"

    rates = []
    n_substituted_rows = 0
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            noisy_text, realised_rate, substituted_types = _apply(
                row["text"], severity, seed=_row_seed(row["post_id"]))
            out_row = Row(
                source_id=row["post_id"],
                split=split,
                condition="codemix",
                severity=severity,
                original_text=row["text"],
                noisy_text=noisy_text,
                label=row["label"],
                realised_noise_rate=realised_rate,
                generator_version=GENERATOR_VERSION,
                n_substitutions=len(substituted_types),
            )
            out_row.validate()
            f.write(json.dumps(out_row.to_dict(), ensure_ascii=False) + "\n")
            rates.append(realised_rate)
            n_substituted_rows += bool(substituted_types)

    avg_rate = sum(rates) / len(rates) if rates else 0.0
    pct_touched = n_substituted_rows / len(rows) if rows else 0.0
    log(f"{split}/{severity}: {len(rows)} rows -> {out_path} "
        f"(mean realised_noise_rate={avg_rate:.3f}, {n_substituted_rows}/{len(rows)} rows touched = {pct_touched:.1%})")
    return {"n_rows": len(rows), "mean_realised_noise_rate": avg_rate,
            "rows_touched": n_substituted_rows, "pct_touched": pct_touched}


def run_demo(path: Path) -> None:
    """Quick, ad-hoc demo: read a JSON list of plain text strings, print
    original/light/heavy codemix output for each. Does not touch
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
