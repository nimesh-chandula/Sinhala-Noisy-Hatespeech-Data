# Code-mix selection: production self-check (pre-round-4 baseline vs. shipping code)

**Status: SELF-CHECK, post-adoption.** The attestation-aware variant compared here was adopted into `src.noisers.codemix._apply()` -- this is no longer a decision document. `new` below calls that real production function directly (imported, not reimplemented), so this script can never silently drift from what actually ships. `old` is a deliberately FROZEN historical snapshot of the pre-round-4 algorithm, kept only to describe where round 4 started from. The original pre-adoption decision record is data/lexicon/codemix_selection_comparison.md and is not touched by this run.

## What changed

Pre-round-4 `_apply()` (frozen reference, `_apply_pre_round4` in this script): forced draw, uniform random, from `plausible` (reviewer-approved) words if any exist in the post, else from the full `eligible` set.

Production `_apply()` (imported live from src.noisers.codemix): same forced draw, same seed, same count contract (`n_substitutions == min(k, pool_size)`), but the pool is chosen by a 4-level priority instead of 2: prefer words that are BOTH reviewer-approved AND have real evidence of being switched by real Sinhala speakers (`data/lexicon/codemix_attested_vocabulary.json`, restricted to its `primary` and `secondary` tiers -- both mined directly from SOLD's own text; the broader `tertiary` tier is pooled loosely across corpora and can register a count of 1-2 from an English quote or scrape noise rather than genuine code-switching, confirmed by `crazy` [tertiary count=2] getting selected here on a first pass despite zero real intrasentential evidence -- so it's excluded from the selection gate, kept only as report-level context); fall back to reviewer-approved-but-unattested only if nothing evidenced is available; fall back further only if nothing reviewer-approved is available at all.

## Headline numbers

- Rows compared: 20000 (train+test x light+heavy)
- Output identical to pre-round-4 baseline: 15124/20000 (75.6%)
- Type-attestation of the WORD ACTUALLY PICKED: **24.4% (pre-round-4) -> 42.4% (production)**
- Touched-post coverage (density): 91.3% (pre-round-4) -> 91.3% (production)
- Mean realised_noise_rate: 0.1051 (pre-round-4) -> 0.0979 (production)
- Posts where a Tier-1/2-flagged word (insult / bare verb) got picked: 0 (pre-round-4 baseline, computed against the CURRENT wordbank so these entries mostly no longer exist to be picked) -> 0 (production; should be 0 -- if not, see eval/invariants.py's check_codemix_no_affect_substitution) — out of 20000 rows

## Rebuttal check — does the redesign still survive the reviewer's original objection?

- Positional JSD vs natural SOLD switches: **0.0025** (0-1 scale; current shipped output measured 0.0017)
- Licensing rate (share followed by an එක/කර/වල/වෙ particle): **0.472** vs natural 0.44

## Which pool actually got used, across all rows

- plausible-only (no attested option): 8564 (42.8%)
- plausible+attested: 7824 (39.1%)
- no eligible candidate: 1736 (8.7%)
- full fallback (neither plausible nor attested): 1578 (7.9%)
- attested-but-not-plausible: 298 (1.5%)

The rows landing in the top level (`plausible+attested`) are ones where the new algorithm's choice is now traceable to a real cited sentence, not just a reviewer's yes/no. Rows still landing in the bottom levels are exactly where no evidence exists either way — those are the cases still resting on judgment, now visible instead of hidden inside a uniform random draw.