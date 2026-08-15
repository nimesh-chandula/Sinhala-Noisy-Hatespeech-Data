"""
Generate the `misspell` noised condition for SOLD, both severities, per
split — real Phase 5 output, not a throwaway sample. Same structure as
scripts/generate_codemix.py / generate_transliteration.py (same per-row
seeding, same Row/validate/write path, same output naming convention the
harness globs for) — see those scripts' docstrings for why each piece is
built the way it is; this one only documents what's specific to misspell.

Input is always the clean Sinhala SOLD text, so only Channel A
(src/noisers/misspell.py) actually fires here — Channel B exists for the
future compound pipeline (misspell running after transliteration) and is
exercised by eval/regression/misspell_latin_typo.json, not by this script.

Writes data/outputs/{split}/misspell_{severity}.jsonl, one schema.Row per
SOLD post, validated before being written. Train and test are processed
and written completely separately — never merged, never cross-referenced.

Run:  python scripts/generate_misspell.py
"""

from __future__ import annotations

import json
import sys
import zlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.noisers.misspell import apply, GENERATOR_VERSION  # noqa: E402
from src.schema import Row  # noqa: E402

SOLD_DIR = REPO_ROOT / "data" / "sold"
OUTPUT_DIR = REPO_ROOT / "data" / "outputs"

SEED = 1337
SEVERITIES = ("light", "heavy")
SPLITS = ("train", "test")


def log(msg: str) -> None:
    print(f"[generate_misspell] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _row_seed(post_id: str) -> int:
    """Deterministic per-row seed from (SEED, post_id) — stable across
    processes/runs (unlike Python's built-in hash()). Same derivation as
    generate_codemix.py/generate_transliteration.py; a shared numeric SEED
    across noiser modules is safe since each apply() call consumes its own
    independent random.Random(seed) instance."""
    return zlib.crc32(f"{SEED}:{post_id}".encode("utf-8"))


def generate_split_severity(split: str, severity: str, rows: list[dict]) -> dict:
    out_dir = OUTPUT_DIR / split
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"misspell_{severity}.jsonl"

    rates = []
    n_touched_rows = 0
    with out_path.open("w", encoding="utf-8") as f:
        for row in rows:
            noisy_text, realised_rate = apply(row["text"], severity, seed=_row_seed(row["post_id"]))
            out_row = Row(
                source_id=row["post_id"],
                split=split,
                condition="misspell",
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
            n_touched_rows += noisy_text != row["text"]

    avg_rate = sum(rates) / len(rates) if rates else 0.0
    pct_touched = n_touched_rows / len(rows) if rows else 0.0
    log(f"{split}/{severity}: {len(rows)} rows -> {out_path} "
        f"(mean realised_noise_rate={avg_rate:.4f}, {n_touched_rows}/{len(rows)} rows touched = {pct_touched:.1%})")
    return {"n_rows": len(rows), "mean_realised_noise_rate": avg_rate,
            "rows_touched": n_touched_rows, "pct_touched": pct_touched}


def main() -> None:
    summary = {}
    for split in SPLITS:
        rows = _load_jsonl(SOLD_DIR / f"{split}.jsonl")
        for severity in SEVERITIES:
            summary[f"{split}/{severity}"] = generate_split_severity(split, severity, rows)
    log("done.")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
