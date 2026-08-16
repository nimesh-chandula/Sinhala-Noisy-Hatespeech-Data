"""
Build the GATE B human-review sample: ~300 items spanning EVERY condition
(clean + the five noised vectors, each at light/heavy severity — 11
buckets total) in one combined sample, for plausibility/label-retention/
intelligibility review across the whole pipeline at once — the final
human checkpoint before Phase 5 is called done (CLAUDE.md's GATE B).

Different in kind from every prior review round in this project: those
were per-lexicon or per-condition ("does THIS mechanism work"); this one
is per-CORPUS ("does the shipped dataset, taken as a whole, look right").

27 items per bucket (11 x 27 = 297, ~300 per CLAUDE.md's own wording).
Drawn from TRAIN only (same convention every review sample in this repo
uses). For the five noised conditions, drawn from CHANGED rows only
(noisy_text != original_text) — same reasoning build_review_sample.py's
--only-changed flag already established: a plain draw over a
sparsely-touched condition (abbreviate's 32.79%, or any condition at
light severity) would waste review slots on rows that are just the
original text, reviewing nothing. `clean` has no "changed" rows by
definition, so it's sampled plainly (itself a valid, if trivial, check:
is the clean condition really just the unmodified original?).

Writes:
  data/outputs/gate_b_sample.jsonl  (raw rows, tagged with condition/severity)
  data/outputs/gate_b_sample.md     (grouped by condition, for reading)

Run:  python scripts/build_gate_b_sample.py
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
N_PER_BUCKET = 27

NOISED_CONDITIONS = ("transliteration", "codemix", "misspell", "abbreviate", "compound")
SEVERITIES = ("light", "heavy")

JSONL_PATH = OUTPUTS_DIR / "gate_b_sample.jsonl"
MD_PATH = OUTPUTS_DIR / "gate_b_sample.md"


def log(msg: str) -> None:
    print(f"[build_gate_b_sample] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def build_sample() -> list[dict]:
    rng = random.Random(SEED)
    sample: list[dict] = []

    clean_rows = _load_jsonl(OUTPUTS_DIR / "train" / "clean.jsonl")
    n = min(N_PER_BUCKET, len(clean_rows))
    sample.extend(rng.sample(clean_rows, n))
    log(f"clean: sampled {n}/{len(clean_rows)}")

    for condition in NOISED_CONDITIONS:
        for severity in SEVERITIES:
            rows = _load_jsonl(OUTPUTS_DIR / "train" / f"{condition}_{severity}.jsonl")
            pool = [r for r in rows if r["noisy_text"] != r["original_text"]]
            if len(pool) < N_PER_BUCKET:
                log(f"WARNING: only {len(pool)} changed rows for {condition}/{severity} "
                    f"(< {N_PER_BUCKET} requested) — sampling all of them")
            n = min(N_PER_BUCKET, len(pool))
            sample.extend(rng.sample(pool, n))
            log(f"{condition}/{severity}: sampled {n}/{len(pool)} changed (of {len(rows)} total)")

    return sample


def write_sample(sample: list[dict]) -> None:
    with JSONL_PATH.open("w", encoding="utf-8") as f:
        for row in sample:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    lines = [
        "# GATE B human review sample",
        "",
        f"{len(sample)} items across all 11 condition x severity buckets "
        f"(clean + 5 noised conditions x light/heavy, {N_PER_BUCKET} each), "
        "drawn from SOLD train only, seed 1337. Noised buckets are drawn from "
        "CHANGED rows only (clean is sampled plainly, since it has none).",
        "",
        "For each: does the noisy text read like something a real person would "
        "type, does it still plausibly carry the same OFF/NOT label as the "
        "original, and is it still intelligible?",
        "",
    ]
    by_bucket: dict[str, list[dict]] = {}
    for row in sample:
        key = f"{row['condition']}/{row['severity']}"
        by_bucket.setdefault(key, []).append(row)

    for key in sorted(by_bucket):
        rows = by_bucket[key]
        lines.append(f"## {key} ({len(rows)} items)")
        lines.append("")
        for i, row in enumerate(rows, 1):
            lines.append(f"### {i}. `{row['source_id']}` — label={'OFF' if row['label'] else 'NOT'}, "
                          f"realised_noise_rate={row['realised_noise_rate']:.2f}")
            lines.append(f"- **original**: {row['original_text']}")
            lines.append(f"- **noisy**: {row['noisy_text']}")
            lines.append("")

    MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote {len(sample)} items -> {JSONL_PATH}")
    log(f"wrote readable version -> {MD_PATH}")


def main() -> None:
    sample = build_sample()
    write_sample(sample)


if __name__ == "__main__":
    main()
