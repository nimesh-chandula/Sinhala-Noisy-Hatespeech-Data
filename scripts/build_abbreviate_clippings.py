"""
Phase 4b, Stage 1a -- derive Channel A of the abbreviation noiser: SINGLE-WORD
clipping (a word gets shorter), as opposed to Channel B's phrase-level
initialism (see scripts/build_abbreviate_initialisms.py).

--- Why not the same "romanize and group by collision" trick misspell used ---
Misspelling's IME-collision mechanism is linguistically airtight: two clusters
either romanize to the same string or they don't. Abbreviation has no such
closed-form test. An early probe (see LOG.md's "Phase 4b" entry / the plan) --
"any two SOLD words sharing a first letter within cluster-level edit distance
2" -- surfaced mostly FALSE positives: totally unrelated words that happen to
look similar (a "very" word paired with a "hey/dude" word, "bastard" paired
with "forgotten"). Anchoring on a shared first LETTER isn't enough signal.

--- The tightened mechanism actually used here ---
For a long word L (clusters c_1..c_n) and a candidate short form S (clusters
d_1..d_k, k<n): require the PREFIX to match exactly up to S's last cluster
(d_1..d_{k-1} == c_1..c_{k-1}), then measure only how far S's FINAL cluster is
from L's remaining TAIL (c_k..c_n) via grapheme-cluster edit distance
(eval.gold_cer.edit_distance, reused rather than reimplemented). This single
rule captures both intended patterns at once:
  - pure trailing truncation (S is an exact prefix of L) -- the tail distance
    is just how many trailing clusters got dropped;
  - final-syllable fusion (e.g. a common "no/not" word's two syllables'
    vowels merging into one, "###@" -> "##" in cluster terms) -- the tail
    distance captures the fused cluster's edit cost against the un-fused
    original tail.
Both L and S must be independently attested in SOLD with frequency >=
FREQ_FLOOR -- real usage on both sides, never a constructed form nobody
types.

--- Confidence tiers (empirically justified, see LOG.md) ---
Measured over SOLD train+test at FREQ_FLOOR=15, MAX_LEN_DROP=2:
  - tail_distance == 1 ("tier 1"): 504 candidate pairs. Spot-checked as
    overwhelmingly genuine Sinhala colloquial clippings (agglutinative
    suffix-drops: "kiyala"-type -> "kiya"-type, "karanna"-type ->
    "karan(a/)"-type, etc.) -- HIGH confidence.
  - tail_distance == 2 ("tier 2"): 5,456 candidate pairs -- markedly noisier
    (spot-check showed several unrelated-word false positives at this
    distance). Reviewing all 5,456 individually isn't a good use of review
    time for the false-positive rate observed, so only the TOP_TIER2_N
    highest-impact tier-2 candidates are surfaced for review; the rest are
    dropped at the mining stage as low-value, not silently included.
Token coverage at tier 1 alone: 16.24% of Sinhala word tokens (453/1,567
word types with freq>=15) -- sparse and concentrated on common function/
discourse words, much closer to codemix's 1.74%-style ceiling than
misspell's 99.4%. 80.5% of SOLD posts contain >=1 tier-1-eligible word,
which is why Channel A uses codemix's FORCED-PER-POST severity model
(light=1, heavy=2 word substitutions, capped at availability) rather than
misspell's probabilistic coverage-corrected model -- a probabilistic model
tuned to a 16% base rate would leave most light-severity posts untouched,
the same problem codemix v1 had at 1.74% coverage.

Writes:
  data/lexicon/abbreviate_clippings.jsonl        frozen, the noiser reads this
  data/lexicon/.abbreviate_clippings.sha256       hash, stamped into GENERATOR_VERSION
  data/lexicon/abbreviate_clippings_review.csv    for marking up corrections
  data/lexicon/abbreviate_clippings_review.md     for reading

Run:  python scripts/build_abbreviate_clippings.py
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

from src.graphemes import clusters, text_runs  # noqa: E402
from eval.gold_cer import edit_distance  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
SOLD_DIR = DATA_DIR / "sold"
LEXICON_DIR = DATA_DIR / "lexicon"

CLIPPINGS_PATH = LEXICON_DIR / "abbreviate_clippings.jsonl"
CLIPPINGS_HASH_PATH = LEXICON_DIR / ".abbreviate_clippings.sha256"
CORRECTIONS_PATH = LEXICON_DIR / "abbreviate_review_corrections.jsonl"
REVIEW_CSV_PATH = LEXICON_DIR / "abbreviate_clippings_review.csv"
REVIEW_MD_PATH = LEXICON_DIR / "abbreviate_clippings_review.md"

FREQ_FLOOR = 15
MAX_LEN_DROP = 2
TOP_TIER2_N = 150
MAX_EXAMPLES = 3


def log(msg: str) -> None:
    print(f"[build_abbreviate_clippings] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sold_word_freq_and_examples() -> tuple[dict[str, int], dict[str, list[str]]]:
    """(word_freq, examples) over every Sinhala word run in SOLD train+test.
    examples[word] holds up to MAX_EXAMPLES full posts the word appeared in,
    for the review file."""
    word_freq: dict[str, int] = defaultdict(int)
    examples: dict[str, list[str]] = defaultdict(list)
    for split in ("train", "test"):
        with (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                text = json.loads(line)["text"]
                seen_words_this_post = set()
                for is_sinhala, run in text_runs(text):
                    if not is_sinhala:
                        continue
                    word_freq[run] += 1
                    if run not in seen_words_this_post:
                        seen_words_this_post.add(run)
                        if len(examples[run]) < MAX_EXAMPLES:
                            examples[run].append(text)
    return dict(word_freq), dict(examples)


def derive_raw_candidates(word_freq: dict[str, int]) -> dict[str, list[dict]]:
    """{long_word: [{"short": ..., "tail_dist": 1|2}, ...]} -- the pure
    derivation step, before corrections or tier-2 capping. See module
    docstring for the exact rule."""
    words = [(w, clusters(w)) for w, f in word_freq.items() if f >= FREQ_FLOOR and len(clusters(w)) >= 2]
    by_first_cluster: dict[str, list[tuple[str, list[str]]]] = defaultdict(list)
    for w, cs in words:
        by_first_cluster[cs[0]].append((w, cs))

    candidates: dict[str, list[dict]] = defaultdict(list)
    for w_long, c_long in words:
        n = len(c_long)
        for w_short, c_short in by_first_cluster.get(c_long[0], []):
            if w_short == w_long:
                continue
            k = len(c_short)
            if k >= n or n - k > MAX_LEN_DROP:
                continue
            if word_freq.get(w_short, 0) < FREQ_FLOOR:
                continue
            if c_short[:k - 1] != c_long[:k - 1]:
                continue
            tail_dist = edit_distance([c_short[k - 1]], c_long[k - 1:])
            if tail_dist <= 2:
                candidates[w_long].append({"short": w_short, "tail_dist": tail_dist})
    return dict(candidates)


def cap_tier2(candidates: dict[str, list[dict]], word_freq: dict[str, int]) -> dict[str, list[dict]]:
    """Keep every tier-1 (tail_dist==1) candidate; keep tier-2 (tail_dist==2)
    candidates only for the TOP_TIER2_N long words by frequency that have
    NO tier-1 candidate at all (a tier-1 candidate is already a better,
    higher-confidence option for that word, so a lower-tier alternative adds
    review burden without adding coverage)."""
    tier1_words = {w for w, cs in candidates.items() if any(c["tail_dist"] == 1 for c in cs)}
    tier2_only = sorted(
        (w for w in candidates if w not in tier1_words),
        key=lambda w: -word_freq.get(w, 0),
    )[:TOP_TIER2_N]
    kept_tier2 = set(tier2_only)

    out: dict[str, list[dict]] = {}
    for w, cs in candidates.items():
        if w in tier1_words:
            out[w] = [c for c in cs if c["tail_dist"] == 1]
        elif w in kept_tier2:
            out[w] = cs
    return out


def merge_corrections(candidates: dict[str, list[dict]]) -> tuple[dict[str, list[dict]], int, int]:
    """Apply data/lexicon/abbreviate_review_corrections.jsonl. Two actions:
      - {"action": "reject_word", "long": ...}: drop every candidate for that
        long word.
      - {"action": "reject_pair", "long": ..., "short": ...}: drop just that
        one (long, short) pair.
    Accumulates across rounds; last line for a given key wins (same
    file-order-dict-overwrite convention as every other corrections merge in
    this repo)."""
    merged = {w: list(cs) for w, cs in candidates.items()}
    n_word_rejected = n_pair_rejected = 0
    for row in _load_jsonl(CORRECTIONS_PATH):
        action = row["action"]
        long = row["long"]
        if action == "reject_word":
            if merged.pop(long, None) is not None:
                n_word_rejected += 1
            continue
        if action == "reject_pair":
            if long in merged:
                before = len(merged[long])
                merged[long] = [c for c in merged[long] if c["short"] != row["short"]]
                if len(merged[long]) < before:
                    n_pair_rejected += 1
                if not merged[long]:
                    del merged[long]
            continue
        raise ValueError(f"unknown correction action {action!r} for long={long!r}")
    return merged, n_word_rejected, n_pair_rejected


def main() -> None:
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)

    word_freq, examples = sold_word_freq_and_examples()
    log(f"SOLD: {len(word_freq)} distinct Sinhala word types, {sum(word_freq.values())} tokens")

    raw_candidates = derive_raw_candidates(word_freq)
    n_tier1 = sum(1 for cs in raw_candidates.values() for c in cs if c["tail_dist"] == 1)
    n_tier2 = sum(1 for cs in raw_candidates.values() for c in cs if c["tail_dist"] == 2)
    log(f"derived candidates for {len(raw_candidates)} long words "
        f"({n_tier1} tier-1 pairs, {n_tier2} tier-2 pairs, pre-cap)")

    capped = cap_tier2(raw_candidates, word_freq)
    n_dropped_tier2 = n_tier2 - sum(1 for cs in capped.values() for c in cs if c["tail_dist"] == 2)
    log(f"capped tier-2 to top {TOP_TIER2_N} words without a tier-1 option "
        f"({n_dropped_tier2} lower-value tier-2 pairs dropped from review entirely)")

    final, n_word_rejected, n_pair_rejected = merge_corrections(capped)
    corrections = _load_jsonl(CORRECTIONS_PATH)
    if corrections:
        log(f"applied {len(corrections)} review corrections: "
            f"{n_word_rejected} words rejected, {n_pair_rejected} pairs rejected")
    log(f"-> {len(final)} long words with >=1 approved short form")

    covered_tokens = sum(word_freq.get(w, 0) for w in final)
    total_tokens = sum(word_freq.values())
    log(f"token coverage: {covered_tokens}/{total_tokens} ({100 * covered_tokens / total_tokens:.2f}%)")

    n_posts_eligible = 0
    n_posts = 0
    eligible_words = set(final)
    for split in ("train", "test"):
        with (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                n_posts += 1
                words_in_post = {run for is_sin, run in text_runs(json.loads(line)["text"]) if is_sin}
                if words_in_post & eligible_words:
                    n_posts_eligible += 1
    log(f"posts with >=1 eligible word: {n_posts_eligible}/{n_posts} "
        f"({100 * n_posts_eligible / n_posts:.1f}%)")

    # --- write frozen artifact ---
    rows_out = []
    for long in sorted(final):
        cand_sorted = sorted(final[long], key=lambda c: (c["tail_dist"], c["short"]))
        rows_out.append({
            "long": long,
            "candidates": [
                {"short": c["short"], "tail_dist": c["tail_dist"], "freq_short": word_freq.get(c["short"], 0)}
                for c in cand_sorted
            ],
            "freq_long": word_freq.get(long, 0),
        })
    with CLIPPINGS_PATH.open("w", encoding="utf-8") as f:
        for row in rows_out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(CLIPPINGS_PATH.read_bytes()).hexdigest()
    CLIPPINGS_HASH_PATH.write_text(digest, encoding="utf-8")
    log(f"wrote {len(rows_out)} long-word entries -> {CLIPPINGS_PATH}")
    log(f"sha256={digest} (first 8: {digest[:8]}) -> {CLIPPINGS_HASH_PATH}")

    # --- write human review artifacts, impact-ordered ---
    ordered = sorted(rows_out, key=lambda r: -r["freq_long"])
    with REVIEW_CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "long", "freq_long", "candidates",
            "example_1", "example_2", "example_3",
            "reject_word", "reject_shorts", "notes",
        ])
        writer.writeheader()
        for r in ordered:
            cand_str = " / ".join(f"{c['short']} (tier{c['tail_dist']}, freq={c['freq_short']})"
                                   for c in r["candidates"])
            exs = examples.get(r["long"], [])
            writer.writerow({
                "long": r["long"], "freq_long": r["freq_long"], "candidates": cand_str,
                "example_1": exs[0] if len(exs) > 0 else "",
                "example_2": exs[1] if len(exs) > 1 else "",
                "example_3": exs[2] if len(exs) > 2 else "",
                "reject_word": "", "reject_shorts": "", "notes": "",
            })
    log(f"wrote review CSV -> {REVIEW_CSV_PATH}")

    lines = [
        "# Abbreviation Channel A (word clipping) review",
        "",
        f"{len(ordered)} long words, impact-ordered by SOLD frequency. Each has one or "
        "more candidate clipped forms, tagged tier1 (tail_dist=1, high confidence -- "
        "spot-checked as overwhelmingly genuine) or tier2 (tail_dist=2, noisier, only "
        f"the top {TOP_TIER2_N} highest-impact words lacking a tier-1 option are included "
        "at all -- see module docstring for why the rest were dropped at the mining stage).",
        "",
        "Reject a whole word (`reject_word`) if NONE of its candidates are real, or "
        "list specific short forms to drop (`reject_shorts`, space-separated) if only "
        "some are wrong. Leave blank to accept as-is. Record corrections in "
        "data/lexicon/abbreviate_review_corrections.jsonl: "
        "{\"action\": \"reject_word\", \"long\": ...} or "
        "{\"action\": \"reject_pair\", \"long\": ..., \"short\": ...}.",
        "",
    ]
    for i, r in enumerate(ordered, 1):
        cand_str = ", ".join(f"`{c['short']}` (tier{c['tail_dist']}, freq={c['freq_short']})"
                              for c in r["candidates"])
        lines.append(f"## {i}. `{r['long']}` (freq={r['freq_long']}) -> {cand_str}")
        for ex in examples.get(r["long"], []):
            lines.append(f"  - {ex}")
        lines.append("")
    REVIEW_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote review MD -> {REVIEW_MD_PATH}")


if __name__ == "__main__":
    main()
