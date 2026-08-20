"""
Codemix round 5, Stage 4b — freeze the two CMI band distributions
src/noisers/codemix.py samples a per-post target from
(data/lexicon/codemix_cmi_bands.json).

  light bands: SOLD's own NATURAL CMI distribution, read directly from
    data/lexicon/codemix_cmi_reference.json (scripts/measure_cmi_
    distribution.py, Stage 0 -- already frozen). An explicit lo=hi=0 band
    carries the (1 - line_rate) mass of posts that are naturally
    monolingual -- the earlier interactive sizing pass folded this into a
    "0-10" band that implicitly excluded true zeros (codemix_cmi_
    reference.json's band shares are computed over MIXED posts only, cmi>0
    -- see its own methodology_note), which would have made light touch
    every single post, not the ~13.3% SOLD's own text actually mixes.

  heavy bands: this corpus's own ACHIEVABLE CEILING, computed by running
    src.noisers.codemix's actual `_find_max_units()` (unbounded -- the
    exact function _apply() uses at generation time) over every SOLD post
    and bucketing the resulting ceiling CMI. Using the noiser's own
    production function here (not a second, hand-written approximation)
    means the measured ceiling and generation-time behaviour can never
    drift apart -- same discipline as eval/invariants.py's "re-derive
    independently" checks, applied in the opposite direction: here it's
    the FREEZE step that must reuse the real code, not reimplement it.

Requires data/lexicon/codemix_wordbank.jsonl, codemix_attested_vocabulary.json,
and codemix_phrasebank.jsonl to already exist (Stages 0-4) -- this is
specifically the LAST piece frozen before generation, since it depends on
everything else.

Run:  python scripts/freeze_codemix_cmi_bands.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _codemix_common import sold_posts, log  # noqa: E402
from src.noisers.codemix import _find_max_units  # noqa: E402

LEXICON_DIR = REPO_ROOT / "data" / "lexicon"
CMI_REFERENCE_PATH = LEXICON_DIR / "codemix_cmi_reference.json"
OUTPUT_PATH = LEXICON_DIR / "codemix_cmi_bands.json"
HASH_PATH = LEXICON_DIR / ".codemix_cmi_bands.sha256"

# Heavy histogram bucket boundaries. Upper bound is generous (100, well
# above the measured p99) rather than tight -- see the module docstring:
# a target_cmi drawn above what a specific post can actually deliver isn't
# harmful, _pack_units_to_budget just uses the full ceiling for that post.
_HEAVY_BUCKETS = [(0, 0), (1, 10), (11, 20), (21, 30), (31, 40), (41, 100)]


def _light_bands_from_reference() -> list[dict]:
    ref = json.loads(CMI_REFERENCE_PATH.read_text(encoding="utf-8"))
    pooled = ref["pooled"]
    line_rate = pooled["line_rate"]
    band_shares = pooled["cmi_band_shares"]  # over MIXED posts only

    bands = [{"lo": 0, "hi": 0, "weight": 1.0 - line_rate}]
    band_bounds = {
        "0-10": (1, 10), "11-20": (11, 20), "21-30": (21, 30),
        "31-40": (31, 40), "41-50": (41, 50), "50+": (51, 100),
    }
    for label, (lo, hi) in band_bounds.items():
        share = band_shares.get(label, 0.0)
        bands.append({"lo": lo, "hi": hi, "weight": line_rate * share})
    return bands


def _heavy_bands_from_ceiling() -> tuple[list[dict], dict]:
    posts = sold_posts()
    ceilings: list[float] = []
    for post in posts:
        runs, units = _find_max_units(post["text"])
        n_words = sum(1 for is_sinhala, _run in runs if is_sinhala)
        if n_words == 0:
            continue
        n_altered = sum(u["n_words"] for u in units)
        ceilings.append(100.0 * n_altered / n_words)

    counts = [0] * len(_HEAVY_BUCKETS)
    for c in ceilings:
        for i, (lo, hi) in enumerate(_HEAVY_BUCKETS):
            if lo <= c <= hi:
                counts[i] += 1
                break
    total = len(ceilings)
    bands = [
        {"lo": float(lo), "hi": float(hi), "weight": counts[i] / total}
        for i, (lo, hi) in enumerate(_HEAVY_BUCKETS)
    ]
    stats = {
        "n_posts": total,
        "mean_ceiling": sum(ceilings) / total,
        "median_ceiling": sorted(ceilings)[total // 2],
        "bucket_counts": {f"{lo}-{hi}": counts[i] for i, (lo, hi) in enumerate(_HEAVY_BUCKETS)},
    }
    return bands, stats


def main() -> None:
    log("freeze_codemix_cmi_bands", "deriving light bands from the frozen natural-CMI reference ...")
    light_bands = _light_bands_from_reference()
    log("freeze_codemix_cmi_bands",
        f"light: {[round(b['weight'], 4) for b in light_bands]} "
        f"(0-band = 1 - natural line_rate)")

    log("freeze_codemix_cmi_bands",
        "computing heavy bands from the real achievable ceiling (running the "
        "noiser's own _find_max_units over all posts) ...")
    heavy_bands, heavy_stats = _heavy_bands_from_ceiling()
    log("freeze_codemix_cmi_bands",
        f"heavy: mean_ceiling={heavy_stats['mean_ceiling']:.2f} "
        f"median={heavy_stats['median_ceiling']:.2f} "
        f"buckets={heavy_stats['bucket_counts']}")

    output = {
        "methodology_note": (
            "light bands = SOLD's own natural CMI distribution (data/lexicon/"
            "codemix_cmi_reference.json), including an explicit 0-weight band "
            "for the ~86.7% of posts that are naturally monolingual. heavy "
            "bands = this corpus's measured achievable ceiling under the "
            "still-fully-intact reviewer-plausibility gate (mean ~16.7, not "
            "the literature's ~27.5 -- see src/noisers/codemix.py's module "
            "docstring 'Round 5' section and docs/research_documentation.md "
            "for the full defense). Computed by scripts/freeze_codemix_cmi_"
            "bands.py, which calls src.noisers.codemix._find_max_units "
            "directly (the SAME function _apply() uses at generation time) "
            "so this measurement can never drift from runtime behaviour."
        ),
        "bands": {"light": light_bands, "heavy": heavy_bands},
        "heavy_ceiling_stats": heavy_stats,
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    digest = hashlib.sha256(OUTPUT_PATH.read_bytes()).hexdigest()
    HASH_PATH.write_text(digest, encoding="utf-8")
    log("freeze_codemix_cmi_bands", f"wrote {OUTPUT_PATH} (sha256 {digest[:8]}...)")


if __name__ == "__main__":
    main()
