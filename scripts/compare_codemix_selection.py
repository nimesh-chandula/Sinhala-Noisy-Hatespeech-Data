"""
Code-mix bank correction round 4 — originally: compare pre-round-4 selection
(uniform random over the plausible/eligible pool) against an
ATTESTATION-AWARE variant (prefer words with real evidence of being switched
by real Sinhala speakers, cited to actual SOLD sentences, before falling
back to unattested words), to decide whether to adopt it.

**That decision is made — the attestation-aware variant was adopted into
src.noisers.codemix._apply() itself.** This script now compares that frozen
historical PRE-round-4 baseline (`_apply_pre_round4` below, a deliberately
frozen snapshot, not meant to track anything) against the REAL PRODUCTION
algorithm (imported directly as `_apply` from src.noisers.codemix, not
re-implemented here) — so a re-run always reflects whatever selection logic
is actually shipping, and can never silently drift from it. Re-running this
script will show close to 100% output agreement between "new" and current
`data/outputs/` (both ARE the production algorithm now) — that's expected,
not a bug; the meaningful comparison is "new" vs the frozen "old" baseline,
same as it always was.

data/lexicon/codemix_selection_comparison.md is the PERMANENT historical
record of the original pre-adoption decision (see the round-4 plan's
documentation section: "keep permanently, as-is") — re-running this script
does NOT overwrite it; pass --out to write anywhere else for a fresh spot
check.

READ-ONLY. Does not touch codemix_wordbank.jsonl, does not regenerate
data/outputs/, does not change src/noisers/codemix.py. Runs both algorithms
over the same 20,000 rows (train+test x light+heavy) with the SAME per-row
seeds generate_codemix.py uses, so the comparison is apples-to-apples.

The new algorithm, per post:
  eligible  = Sinhala words in the post that are wordbank keys       (same as current)
  plausible = eligible ∩ codemix_plausible==True                     (same as current)
  attested  = eligible words whose English headword has ANY evidence
              in data/lexicon/codemix_attested_vocabulary.json
  Priority order (first non-empty pool wins):
    1. plausible ∩ attested   -- reviewed AND evidenced
    2. plausible              -- reviewed, no evidence found          (= current's pool)
    3. eligible ∩ attested    -- evidenced, not reviewed as plausible
    4. eligible                -- current's final fallback
  Same rng.sample(pool, k) draw as _apply() once the pool is fixed, so
  determinism and the count contract (n_substitutions == min(k, pool_size))
  are unchanged -- only WHICH pool is drawn from changes.

This mirrors codemix_plausible's own two-level fallback (prefer plausible,
fall back to eligible) one layer deeper: prefer plausible+evidenced, only
give up evidence when nothing evidenced is plausible, only give up
plausibility when nothing plausible is eligible at all.

Writes:
  data/lexicon/codemix_selection_comparison.md   (the comparison report)

Run:  python scripts/compare_codemix_selection.py
"""

from __future__ import annotations

import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from src.graphemes import text_runs  # noqa: E402
from src.noisers.codemix import _apply as _apply_production  # noqa: E402
from src.noisers.codemix import _load_wordbank, _WORDS_PER_POST  # noqa: E402
from generate_codemix import _row_seed  # noqa: E402

OUTPUTS_DIR = REPO_ROOT / "data" / "outputs"
SOLD_DIR = REPO_ROOT / "data" / "sold"
LEXICON_DIR = REPO_ROOT / "data" / "lexicon"
ATTESTED_PATH = LEXICON_DIR / "codemix_attested_vocabulary.json"
MD_PATH = LEXICON_DIR / "codemix_selection_comparison.md"

_LAT = re.compile(r"^[A-Za-z][A-Za-z\-]{1,}$")
_SIN = re.compile(r"^[඀-෿‍]+$")
_SINANY = re.compile(r"[඀-෿]")
_SKIP = {"url", "user", "rt", "lka", "srilanka", "lanka", "sri"}
_STRIP = ".,!?\"'()[]{}#@:;‘’“”"


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _headword(english: str) -> str:
    return english.split()[0].lower().strip(".,") if english else ""


def _apply_pre_round4(text: str, severity: str, seed: int, wordbank: dict):
    """Deliberately FROZEN snapshot of src.noisers.codemix._apply() as it
    existed before round 4: uniform draw over plausible (falling back to
    eligible), no attestation preference. This is a historical reference
    point, not production code -- it must NOT be "kept in sync" with
    anything; its entire purpose is to keep describing round 4's BEFORE
    state even as production code moves on. See _apply_production (the real
    src.noisers.codemix._apply, imported directly above) for the AFTER
    state -- that one only ever reflects whatever is actually shipping."""
    k = _WORDS_PER_POST[severity]
    runs = list(text_runs(text))
    sinhala_words = [run for is_sin, run in runs if is_sin]
    n_words = len(sinhala_words)

    eligible = sorted({w for w in sinhala_words if w in wordbank})
    plausible = [w for w in eligible if wordbank[w]["codemix_plausible"]]
    pool = plausible if plausible else eligible

    rng = random.Random(seed)
    chosen = set(rng.sample(pool, min(k, len(pool))))

    out_parts = []
    n_altered = 0
    for is_sin, run in runs:
        if is_sin and run in chosen:
            out_parts.append(wordbank[run]["english"])
            n_altered += 1
        else:
            out_parts.append(run)
    rate = (n_altered / n_words) if n_words else 0.0
    return "".join(out_parts), rate, sorted(chosen)


def _pool_level(sinhala_words: list[str], wordbank: dict, attested: dict) -> str:
    """Pure reporting label ONLY -- classifies which of the 4 priority
    levels a post's pool falls into, independently of whichever function
    actually performs the draw, so this can annotate _apply_production's
    real output without needing that function to expose its internals."""
    eligible = sorted({w for w in sinhala_words if w in wordbank})
    plausible = [w for w in eligible if wordbank[w]["codemix_plausible"]]
    is_attested = lambda w: attested.get(_headword(wordbank[w]["english"]), {}).get("tier") in ("primary", "secondary")
    if not eligible:
        return "no eligible candidate"
    if [w for w in plausible if is_attested(w)]:
        return "plausible+attested"
    if plausible:
        return "plausible-only (no attested option)"
    if [w for w in eligible if is_attested(w)]:
        return "attested-but-not-plausible"
    return "full fallback (neither plausible nor attested)"


def _natural_positional_and_licensing(rows_with_new_text: list[tuple[str, int]]):
    """Recompute the two rebuttal metrics (positional JSD, licensor rate)
    against the NEW algorithm's output, to confirm the redesign doesn't
    undo the position/licensing result the removal-round justification
    rests on. `rows_with_new_text` is [(noisy_text, n_sinhala_words_in_post), ...]
    -- not needed directly; we recompute straight from text."""
    pos = Counter()
    licensed = 0
    total = 0
    followers = Counter()
    licensor_prefixes = ("එක", "කර", "වල", "වෙ")
    for text, _ in rows_with_new_text:
        words = [w.strip(_STRIP) for w in text.split()]
        for i in range(1, len(words) - 1):
            w = words[i]
            if _LAT.match(w) and w.lower() not in _SKIP and _SIN.match(words[i - 1]) and _SIN.match(words[i + 1]):
                total += 1
                nxt = words[i + 1]
                followers[nxt] += 1
                if any(nxt.startswith(p) for p in licensor_prefixes):
                    licensed += 1
                if len(words) > 2:
                    pos[int(i / (len(words) - 1) * 10)] += 1
    dist = [pos[b] / total for b in range(11)] if total else [0.0] * 11
    return dist, (licensed / total if total else 0.0), total


def _natural_position_baseline() -> list[float]:
    pos = Counter()
    total = 0
    for split in ("train", "test"):
        for row in _load_jsonl(SOLD_DIR / f"{split}.jsonl"):
            text = row["text"]
            if not _SINANY.search(text):
                continue
            words = [w.strip(_STRIP) for w in text.split()]
            if len(words) < 3:
                continue
            for i in range(1, len(words) - 1):
                w = words[i]
                if _LAT.match(w) and w.lower() not in _SKIP and _SIN.match(words[i - 1]) and _SIN.match(words[i + 1]):
                    total += 1
                    pos[int(i / (len(words) - 1) * 10)] += 1
    return [pos[b] / total for b in range(11)] if total else [0.0] * 11


def _jsd(p: list[float], q: list[float]) -> float:
    m = [(a + b) / 2 for a, b in zip(p, q)]
    kl = lambda a, b: sum(x * math.log2(x / y) for x, y in zip(a, b) if x > 0 and y > 0)
    return (kl(p, m) + kl(q, m)) / 2


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=LEXICON_DIR / "codemix_selection_self_check.md",
                         help="where to write the report -- deliberately NOT codemix_selection_comparison.md "
                              "by default, since that file is the permanent historical pre-adoption record "
                              "and must not be silently overwritten by a post-adoption self-check run")
    args = parser.parse_args()

    wordbank = _load_wordbank()
    attested = json.loads(ATTESTED_PATH.read_text(encoding="utf-8")) if ATTESTED_PATH.exists() else {}
    if not wordbank:
        print("[compare_codemix_selection] wordbank missing")
        return
    if not attested:
        print("[compare_codemix_selection] attestation index missing — run build_codemix_attestation.py first")
        return

    labels: dict[str, int] = {}
    for split in ("train", "test"):
        for row in _load_jsonl(SOLD_DIR / f"{split}.jsonl"):
            labels[row["post_id"]] = row["label"]

    n_rows = 0
    n_identical = 0
    level_counts: Counter = Counter()
    old_type_attested = 0
    new_type_attested = 0
    old_total_subs = 0
    new_total_subs = 0
    old_touched = 0
    new_touched = 0
    old_tier_hits = Counter()  # pre-round-4 baseline choosing an affect/bare-verb word
    new_tier_hits = Counter()  # production choosing the same -- expect ~0: those entries are REMOVED
    # from the CURRENT (post-round-4) wordbank now, not merely deprioritized, so this can only
    # register a hit for a word that somehow survived removal -- see check_codemix_no_affect_substitution
    # in eval/invariants.py for the authoritative version of this guarantee.
    flagged_words = set()
    abusive_headwords = {"maniac", "crazy", "idiot", "fool", "stupid", "dog", "pig", "devil", "demon",
                          "traitor", "thief", "liar", "shit", "moron", "beast", "swine"}
    for sinhala, entry in wordbank.items():
        if _headword(entry["english"]) in abusive_headwords:
            flagged_words.add(sinhala)

    new_texts_for_metrics: list[tuple[str, int]] = []
    old_rate_sum, new_rate_sum = 0.0, 0.0

    for split in ("train", "test"):
        for severity in ("light", "heavy"):
            rows = _load_jsonl(OUTPUTS_DIR / split / f"codemix_{severity}.jsonl")
            for row in rows:
                n_rows += 1
                seed = _row_seed(row["source_id"])
                old_text, old_rate, old_chosen = _apply_pre_round4(row["original_text"], severity, seed=seed, wordbank=wordbank)
                new_text, new_rate, new_chosen = _apply_production(row["original_text"], severity, seed=seed)
                sinhala_words = [r for is_sin, r in text_runs(row["original_text"]) if is_sin]
                level = _pool_level(sinhala_words, wordbank, attested) if new_chosen else "no eligible candidate"

                old_rate_sum += old_rate
                new_rate_sum += new_rate
                if old_text == new_text:
                    n_identical += 1
                level_counts[level] += 1

                old_touched += bool(old_chosen)
                new_touched += bool(new_chosen)
                old_total_subs += len(old_chosen)
                new_total_subs += len(new_chosen)
                _is_att = lambda w: attested.get(_headword(wordbank[w]["english"]), {}).get("tier") in ("primary", "secondary")
                old_type_attested += sum(1 for w in old_chosen if _is_att(w))
                new_type_attested += sum(1 for w in new_chosen if _is_att(w))
                old_tier_hits[bool(set(old_chosen) & flagged_words)] += 1
                new_tier_hits[bool(set(new_chosen) & flagged_words)] += 1

                if severity == "light":
                    new_texts_for_metrics.append((new_text, labels.get(row["source_id"], 0)))

    print(f"[compare_codemix_selection] {n_rows} rows compared; "
          f"{n_identical}/{n_rows} identical ({n_identical/n_rows:.1%})")
    print(f"[compare_codemix_selection] pool level used: {dict(level_counts)}")
    print(f"[compare_codemix_selection] type-attestation: old={old_type_attested/old_total_subs:.1%} "
          f"new={new_type_attested/new_total_subs:.1%}")
    print(f"[compare_codemix_selection] touched-post coverage: old={old_touched/n_rows:.1%} new={new_touched/n_rows:.1%}")
    print(f"[compare_codemix_selection] mean realised_noise_rate: old={old_rate_sum/n_rows:.4f} new={new_rate_sum/n_rows:.4f}")
    print(f"[compare_codemix_selection] posts choosing a tier-1/2-flagged word: "
          f"old={old_tier_hits[True]} new={new_tier_hits[True]}")

    natural_pos = _natural_position_baseline()
    new_pos, new_lic, new_n = _natural_positional_and_licensing(new_texts_for_metrics)
    jsd_val = _jsd(natural_pos, new_pos)
    print(f"[compare_codemix_selection] NEW algorithm rebuttal check: positional JSD={jsd_val:.4f}, "
          f"licensing_rate={new_lic:.3f} (n={new_n})")

    lines = [
        "# Code-mix selection: production self-check (pre-round-4 baseline vs. shipping code)",
        "",
        "**Status: SELF-CHECK, post-adoption.** The attestation-aware variant compared here "
        "was adopted into `src.noisers.codemix._apply()` -- this is no longer a decision "
        "document. `new` below calls that real production function directly (imported, not "
        "reimplemented), so this script can never silently drift from what actually ships. "
        "`old` is a deliberately FROZEN historical snapshot of the pre-round-4 algorithm, kept "
        "only to describe where round 4 started from. The original pre-adoption decision "
        "record is data/lexicon/codemix_selection_comparison.md and is not touched by this run.",
        "",
        "## What changed",
        "",
        "Pre-round-4 `_apply()` (frozen reference, `_apply_pre_round4` in this script): forced "
        "draw, uniform random, from `plausible` (reviewer-approved) words if any exist in the "
        "post, else from the full `eligible` set.",
        "",
        "Production `_apply()` (imported live from src.noisers.codemix): same forced draw, "
        "same seed, same count contract "
        "(`n_substitutions == min(k, pool_size)`), but the pool is chosen by a "
        "4-level priority instead of 2: prefer words that are BOTH reviewer-approved "
        "AND have real evidence of being switched by real Sinhala speakers "
        "(`data/lexicon/codemix_attested_vocabulary.json`, restricted to its `primary` "
        "and `secondary` tiers -- both mined directly from SOLD's own text; the "
        "broader `tertiary` tier is pooled loosely across corpora and can register a "
        "count of 1-2 from an English quote or scrape noise rather than genuine "
        "code-switching, confirmed by `crazy` [tertiary count=2] getting selected "
        "here on a first pass despite zero real intrasentential evidence -- so it's "
        "excluded from the selection gate, kept only as report-level context); fall "
        "back to reviewer-approved-but-unattested only if nothing evidenced is "
        "available; fall back further only if nothing reviewer-approved is available "
        "at all.",
        "",
        "## Headline numbers",
        "",
        f"- Rows compared: {n_rows} (train+test x light+heavy)",
        f"- Output identical to pre-round-4 baseline: {n_identical}/{n_rows} ({n_identical/n_rows:.1%})",
        f"- Type-attestation of the WORD ACTUALLY PICKED: "
        f"**{old_type_attested/old_total_subs:.1%} (pre-round-4) -> {new_type_attested/new_total_subs:.1%} (production)**",
        f"- Touched-post coverage (density): {old_touched/n_rows:.1%} (pre-round-4) -> {new_touched/n_rows:.1%} (production)",
        f"- Mean realised_noise_rate: {old_rate_sum/n_rows:.4f} (pre-round-4) -> {new_rate_sum/n_rows:.4f} (production)",
        f"- Posts where a Tier-1/2-flagged word (insult / bare verb) got picked: "
        f"{old_tier_hits[True]} (pre-round-4 baseline, computed against the CURRENT wordbank so "
        f"these entries mostly no longer exist to be picked) -> {new_tier_hits[True]} (production; "
        f"should be 0 -- if not, see eval/invariants.py's check_codemix_no_affect_substitution) "
        f"— out of {n_rows} rows",
        "",
        "## Rebuttal check — does the redesign still survive the reviewer's original objection?",
        "",
        f"- Positional JSD vs natural SOLD switches: **{jsd_val:.4f}** (0-1 scale; current shipped output measured 0.0017)",
        f"- Licensing rate (share followed by an එක/කර/වල/වෙ particle): **{new_lic:.3f}** vs natural 0.44",
        "",
        "## Which pool actually got used, across all rows",
        "",
    ]
    for level, count in sorted(level_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {level}: {count} ({count/n_rows:.1%})")
    lines.append("")
    lines.append(
        "The rows landing in the top level (`plausible+attested`) are ones where the new "
        "algorithm's choice is now traceable to a real cited sentence, not just a "
        "reviewer's yes/no. Rows still landing in the bottom levels are exactly where "
        "no evidence exists either way — those are the cases still resting on judgment, "
        "now visible instead of hidden inside a uniform random draw."
    )

    args.out.write_text("\n".join(lines), encoding="utf-8")
    print(f"[compare_codemix_selection] wrote {args.out}")


if __name__ == "__main__":
    main()
