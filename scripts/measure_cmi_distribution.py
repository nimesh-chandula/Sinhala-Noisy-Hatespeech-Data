"""
Codemix round 5, Stage 0 — freeze the calibration target BEFORE any noiser
code changes (golden rule 1: build the verifier before the thing it
verifies). Measures SOLD's own natural Code-Mixing Index (CMI), switch-
point fraction (SPF), and I-index distribution, using eval/cmi.py's metric
implementations and scripts/measure_codemix_rate.py's already-validated
LID (the Swa-Bhasha negative filter + loanword table + scrape-artifact
cleaning) — reused rather than reinvented so the "natural" reference and
any later "generated" measurement use the exact same classification rule.

Also re-derives the unigram-lexicon attrition table that ruled out
"translate more single words" as a way to reach the literature's ~27.5
mean-CMI target (see the plan, "What was measured" section 2): for the
TOP_N=4 candidate set that was actually mined and translated, what
fraction of candidate types ended up in-bank, and of those, reviewer-
plausible. This script re-computes it live from the frozen files rather
than hardcoding the number this session found interactively, so a future
re-run after any lexicon change reflects reality, not a stale citation.

Writes data/lexicon/codemix_cmi_reference.json (+ sha256 sidecar) — the
frozen calibration target `_CMI_BANDS` in src/noisers/codemix.py is
designed against, and what eval/harness.py's future CMI checks compare
generated output to.

Requires the .venv interpreter (aksharamukha dependency via
measure_codemix_rate.py's loanword table — see that script's docstring).

Run:  .venv/Scripts/python.exe scripts/measure_cmi_distribution.py
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

from eval import cmi as cmi_mod  # noqa: E402
from _codemix_common import is_candidate_word, sold_posts, text_runs  # noqa: E402
from src.noisers.codemix import _load_wordbank  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
SOLD_DIR = DATA_DIR / "sold"
LEXICON_DIR = DATA_DIR / "lexicon"
OUTPUT_PATH = LEXICON_DIR / "codemix_cmi_reference.json"
HASH_PATH = LEXICON_DIR / ".codemix_cmi_reference.sha256"

TOP_N_PER_POST = 4  # must match scripts/select_codemix_targets.py


def log(msg: str) -> None:
    print(f"[measure_cmi_distribution] {msg}")


def compute_unigram_attrition() -> dict:
    """Re-derive the attrition table: of the SAME TOP_N=4 candidate set
    select_codemix_targets.py actually mined, how many types made it
    in-bank, and of those, how many are reviewer-plausible? This is what
    rules out raising TOP_N_PER_POST as a way to reach a higher CMI target
    — see the plan's "What was measured" section 2 for the full argument."""
    posts = sold_posts()
    wordbank = _load_wordbank()

    freq: dict[str, int] = {}
    for post in posts:
        for w in {r for is_sinhala, r in text_runs(post["text"]) if is_sinhala}:
            if is_candidate_word(w):
                freq[w] = freq.get(w, 0) + 1

    candidates: set[str] = set()
    for post in posts:
        words = [r for is_sinhala, r in text_runs(post["text"]) if is_sinhala]
        top = sorted(
            {w for w in words if is_candidate_word(w)}, key=lambda w: -freq.get(w, 0)
        )[:TOP_N_PER_POST]
        candidates.update(top)

    in_bank = candidates & wordbank.keys()
    plausible = {w for w in in_bank if wordbank[w]["codemix_plausible"]}

    return {
        "top_n_per_post": TOP_N_PER_POST,
        "n_candidate_types": len(candidates),
        "n_in_bank": len(in_bank),
        "in_bank_rate": len(in_bank) / len(candidates) if candidates else 0.0,
        "n_plausible": len(plausible),
        "plausible_rate_of_candidates": len(plausible) / len(candidates) if candidates else 0.0,
        "plausible_rate_of_in_bank": len(plausible) / len(in_bank) if in_bank else 0.0,
    }


def main() -> None:
    if not cmi_mod.is_available():
        log(f"ABORT: {cmi_mod.unavailable_reason()}")
        log("this script requires the venv interpreter -- run with "
            ".venv/Scripts/python.exe, not plain python")
        sys.exit(1)

    LEXICON_DIR.mkdir(parents=True, exist_ok=True)

    log("building Swa-Bhasha attested-Sinhala set (LID negative filter) ...")
    attested = cmi_mod.build_attested_set()

    all_texts: list[str] = []
    per_split: dict[str, list[str]] = {}
    for split in ("train", "test"):
        rows = [json.loads(line) for line in (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8") if line.strip()]
        texts = [r["text"] for r in rows]
        per_split[split] = texts
        all_texts.extend(texts)
        log(f"loaded {len(texts)} posts from {split}")

    log("computing natural CMI/SPF/I-index over train+test (pooled) ...")
    pooled_stats = cmi_mod.corpus_cmi_stats(all_texts, attested)
    log(f"pooled: n_posts={pooled_stats['n_posts']} n_mixed={pooled_stats['n_mixed']} "
        f"line_rate={pooled_stats['line_rate']:.4f} cmi_mean={pooled_stats['cmi_mean']:.2f} "
        f"spf_mean={pooled_stats['spf_mean']:.3f}")

    per_split_stats = {}
    for split, texts in per_split.items():
        stats = cmi_mod.corpus_cmi_stats(texts, attested)
        per_split_stats[split] = stats
        log(f"{split}: n_mixed={stats['n_mixed']} line_rate={stats['line_rate']:.4f} "
            f"cmi_mean={stats['cmi_mean']:.2f}")

    log("re-deriving unigram-lexicon attrition table ...")
    attrition = compute_unigram_attrition()
    log(f"attrition: {attrition['n_candidate_types']} candidate types -> "
        f"{attrition['n_in_bank']} in-bank ({attrition['in_bank_rate']:.1%}) -> "
        f"{attrition['n_plausible']} plausible ({attrition['plausible_rate_of_candidates']:.1%} of candidates)")

    output = {
        "methodology_note": (
            "Natural CMI/SPF/I-index measured on SOLD train+test using "
            "eval/cmi.py, reusing scripts/measure_codemix_rate.py's LID "
            "(Swa-Bhasha negative filter + loanword table + Twitter-scrape "
            "artifact cleaning). Band shares, SPF, and I-index are computed "
            "over CODE-MIXED posts only (cmi > 0); line_rate reports the "
            "share of ALL posts that are mixed at all, computed separately. "
            "See docs/research_documentation.md for the full write-up and "
            "the plan's citations (Das & Gambäck 2014, Pratapa et al. 2018, "
            "Guzmán et al. 2017)."
        ),
        "pooled": pooled_stats,
        "per_split": per_split_stats,
        "unigram_lexicon_attrition": attrition,
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    digest = hashlib.sha256(OUTPUT_PATH.read_bytes()).hexdigest()
    HASH_PATH.write_text(digest, encoding="utf-8")
    log(f"wrote {OUTPUT_PATH} (sha256 {digest[:8]}...)")


if __name__ == "__main__":
    main()
