# Code-mix selection: current vs. attestation-aware (comparison, not yet applied)

**Status: COMPARISON ONLY.** Neither algorithm below has been written to data/outputs/. This report exists to decide whether to adopt the attestation-aware variant as the real generator before regenerating anything.

## What changed

Current `_apply()`: forced draw, uniform random, from `plausible` (reviewer-approved) words if any exist in the post, else from the full `eligible` set.

New `_apply_attested()`: same forced draw, same seed, same count contract (`n_substitutions == min(k, pool_size)`), but the pool is chosen by a 4-level priority instead of 2: prefer words that are BOTH reviewer-approved AND have real evidence of being switched by real Sinhala speakers (`data/lexicon/codemix_attested_vocabulary.json`, restricted to its `primary` and `secondary` tiers -- both mined directly from SOLD's own text; the broader `tertiary` tier is pooled loosely across corpora and can register a count of 1-2 from an English quote or scrape noise rather than genuine code-switching, confirmed by `crazy` [tertiary count=2] getting selected here on a first pass despite zero real intrasentential evidence -- so it's excluded from the selection gate, kept only as report-level context); fall back to reviewer-approved-but-unattested only if nothing evidenced is available; fall back further only if nothing reviewer-approved is available at all.

## Headline numbers

- Rows compared: 20000 (train+test x light+heavy)
- Output identical to current: 14961/20000 (74.8%)
- Type-attestation of the WORD ACTUALLY PICKED: **23.4% (current) -> 41.6% (new)**
- Touched-post coverage (density): 93.4% (current) -> 93.4% (new)
- Mean realised_noise_rate: 0.1100 (current) -> 0.1026 (new)
- Posts where a Tier-1/2-flagged word (insult / bare verb) got picked: 825 (current) -> 632 (new) — out of 20000 rows, no bank edit involved

## Rebuttal check — does the redesign still survive the reviewer's original objection?

- Positional JSD vs natural SOLD switches: **0.0026** (0-1 scale; current shipped output measured 0.0017)
- Licensing rate (share followed by an එක/කර/වල/වෙ particle): **0.464** vs natural 0.44

## Which pool actually got used, across all rows

- plausible-only (no attested option): 8882 (44.4%)
- plausible+attested: 7864 (39.3%)
- full fallback (neither plausible nor attested): 1614 (8.1%)
- no eligible candidate: 1320 (6.6%)
- attested-but-not-plausible: 320 (1.6%)

The rows landing in the top level (`plausible+attested`) are ones where the new algorithm's choice is now traceable to a real cited sentence, not just a reviewer's yes/no. Rows still landing in the bottom levels are exactly where no evidence exists either way — those are the cases still resting on judgment, now visible instead of hidden inside a uniform random draw.

## Honest limit: this does NOT by itself solve the insult-translation problem

632 rows still pick a Tier-1/2-flagged word (down from 825, a ~23% cut, not an elimination). Checked why, on train/light (209 of the 632):

- **107/209** — the flagged word was the *only* reviewer-approved candidate anywhere in that post. No amount of "prefer evidence" logic changes what's available in a specific post; if `පිස්සු` is the only plausible word present, it gets picked regardless of the selection policy.
- **74/209** — other plausible words existed too, but none had SOLD-grounded evidence either, so the draw among them stayed uniform random and happened to land on the insult anyway.
- **28/209** — neither plausible nor attested: the full fallback pool, same as current behaviour today.

**Conclusion: the two mechanisms are complementary, not substitutes.** Attestation-aware selection is a real, evidence-backed upgrade to word choice generally (higher attestation, same coverage, rebuttal intact) — but it's a *preference*, and a preference can't guarantee zero when the only option in a post is the thing being avoided. Guaranteeing zero insult-translation (the label-integrity requirement from round 4's Tier 1) still needs the explicit hard removal already proposed in `codemix_removals_round4.md` — this redesign doesn't replace that, it sits alongside it and improves everything else the removal list doesn't touch.