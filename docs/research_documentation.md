# Research Documentation — Sinhala Noise Dataset Builder

**Purpose of this document:** a complete, factually-precise reference of
data sources, methodology, tools tested, metrics, and results produced
during this project, intended as raw material for a research paper — not
polished paper prose. Every number below is sourced from a specific file
in the repository (cited inline) so it can be independently re-verified.

**Status as of writing:** Phases 0-2 (verifier, romanizer selection,
transliteration noiser) are complete, including their manual-review
checkpoint and fixes — see §8. Phase 3 (code-mixing noiser) is complete
and generated, paused at its own manual-review checkpoint before Phase 4
begins — see §9.

---

## 1. Project overview

**Objective:** build a pipeline that transforms the clean SOLD Sinhala
hate-speech dataset into "noised" variants — text rendered the way people
actually type Sinhala online (romanized/"Singlish", code-mixed with
English, misspelled, abbreviated) — at two severity levels, for
benchmarking hate-speech detection models under realistic input noise.

**Design principle (governs all methodology below):** *build the verifier
before the thing it verifies.* Before any noise-generation component was
written, an evaluation harness was built that defines pass/fail invariants
and quantitative metrics; every subsequent design decision was accepted or
rejected strictly by whether it improved the harness's measured output,
not by inspection or intuition alone.

**Phase structure:**
| Phase | Goal | Status |
|---|---|---|
| 0 | Build the verifier (harness, metrics, gold/reference data) | Complete |
| 1 | Select a Sinhala→Romanized ("Singlish") conversion backend | Complete |
| 2 | Build the transliteration noiser; generate real output | Complete |
| 3 | Build the code-mixing noiser; generate real output | Complete, paused at manual review |
| 4 (not started) | Misspelling / abbreviation noise vectors | — |
| 5 (not started) | Full dataset generation | — |

---

## 2. Data sources

### 2.1 SOLD (Sinhala Offensive Language Dataset)

- **Source:** `sinhala-nlp/SOLD` on HuggingFace, fetched directly over HTTP
  (`https://huggingface.co/datasets/sinhala-nlp/SOLD/resolve/main/SOLD_{train,test}.tsv`),
  not via the `datasets` library, to keep the dependency footprint small
  and the fetch fully deterministic and hash-verifiable.
- **Exact counts** (verified against the file contents, recorded in
  `data/PROVENANCE.json`):

  | split | rows | offensive rate | file sha256 |
  |---|---|---|---|
  | train | 7,500 | 42.35% | `d2659246313fbcb3dcc9106e47c1caf1806f2946bb77d1f36839d2a0785ae8ad` |
  | test | 2,500 | 40.60% | `e2df6b690da12a704bcb49164d73958ca14c603d977ad0e7826ba071eff32a40` |
  | **total** | **10,000** | **41.9%** | — |

  These match the SOLD paper's reported figures (~10k posts, ~41%
  offensive), confirmed as an explicit invariant (`sold_counts_match_paper`
  in `eval/invariants.py`) rather than assumed.
- **Columns used:** `post_id`, `text`, `label` (`OFF`/`NOT`, mapped to
  1/0). `tokens` and `rationales` columns exist in the source but are
  passed through unused.
- **A third split, `SOLD_trial.tsv` (500 rows), was excluded entirely** —
  it contains 17 duplicate `post_id` values, which would have violated the
  project's split-isolation requirements.
- **Split isolation:** verified that no `post_id` appears in both train
  and test (both at fetch time and as a standing invariant that re-checks
  the persisted data on every harness run).

### 2.2 Swa-Bhasha (Sinhala ↔ Romanized-Sinhala parallel data)

Used for two purposes: (a) a gold standard to score romanizer accuracy
against, and (b) a reference corpus of genuine romanized Sinhala to score
"realism" (distributional similarity) against.

**Provenance chain** (this took real investigation — documented here since
it materially affected the methodology):
1. The dataset's GitHub repository
   (`Sumanathilaka/Swa-Bhasha-Sinhala-Singlish-Dataset`) **contains no
   data at all** — only a README pointing to four Kaggle dataset pages.
2. The Kaggle-hosted files are downloadable anonymously (no API token
   required), but are **UTF-16-encoded Excel exports** with heavy
   trailing-tab padding inside quoted fields, and approximately 15% of
   rows have emoji/special characters corrupted to literal `????`
   sequences.
3. The same author (`deshanksuman`) separately publishes **clean UTF-8 CSV
   mirrors of the same underlying data on HuggingFace**, which is what
   this project actually uses:
   - `deshanksuman/SwaBhasha_Transliteration_Sinhala/test.csv` — sentence-level pairs
   - `deshanksuman/Swabhasha_RomanizedSinhala_Dataset/train.csv` — word-level pairs

**Sentence-level source** (`swabhasha_sentences` in `data/PROVENANCE.json`):
- URL: `https://huggingface.co/datasets/deshanksuman/SwaBhasha_Transliteration_Sinhala/resolve/main/test.csv`
- sha256: `96a5d3309d9816fec66e4abaf06f0ef515d77f3dfccd425440ced2bdef690bae`
- 12,123 raw rows → **11,929 valid unique pairs** after filtering
  (mean 10.9 words per sentence). These are genuine human-typed
  social-media text, not synthetic.
- **Caveat discovered during human review:** this corpus mixes genuine
  casual social-media comments with formal/encyclopedic prose (temple
  histories, biology, historical narrative) — roughly 5.8% of lines exceed
  25 words (clearly expository register), and this formal-register
  material is interleaved evenly throughout the file, not separable by
  position. Decision: left as-is (see §8 for the downstream consequence).

**Word-level source** (`swabhasha_words` in `data/PROVENANCE.json`):
- URL: `https://huggingface.co/datasets/deshanksuman/Swabhasha_RomanizedSinhala_Dataset/resolve/main/train.csv`
- sha256: `ac78cdd5865f5aa1e27023af2f7a2bd90350a63218c126115c53f600ba8aee15`
- 7,122,355 raw rows → **450,207 distinct valid Sinhala words**, mean
  15.76 attested romanizations per word (max 2,048).
- **Important methodological note:** the number of variants per word is
  always an exact power of two (2048, 1024, 512, …), which reveals these
  romanizations are **combinatorially generated** by toggling suffix
  patterns (e.g. `ay`/`aya`/`y`/`ya`) rather than collected from observed
  usage. This makes the data an excellent **multi-reference target for
  CER** (it enumerates the plausible spelling space for a word) but
  explicitly **unsuitable as a realism/distributional reference corpus**
  (its character-n-gram statistics reflect a generation rule, not real
  human typing frequency).

### 2.3 Gold set construction (for romanizer CER scoring)

Built deterministically (seed = 1337) by `scripts/fetch_data.py`:
- **`data/gold/gold_words.jsonl`** — 2,000 Sinhala words sampled from the
  450,207-word vocabulary, each stored with its full set of attested
  romanization variants. Used for the primary CER metric (§3.1).
- **`data/gold/gold_sentences.jsonl`** — 400 real sentence pairs held out
  from the 11,929 valid sentence-level pairs.
- **`data/gold/heldout_words.txt`** — the same 2,000 sampled words, kept as
  an explicit exclusion list. Purpose: when Phase 2 later built a
  word-variant lookup table for the transliteration noiser (§6), it was
  built only from SOLD's own vocabulary *excluding* these 2,000 words —
  otherwise the noiser's spelling-variance mechanism could have leaked the
  gold set's own answers into the pipeline being scored against it.
- **Disjointness guarantee:** the gold sentences and the reference corpus
  (§2.4) are disjoint by construction — a handful of duplicate short
  phrases (e.g. "Patta") that would otherwise appear in both were dropped
  from the reference set rather than allowed to overlap. This is enforced
  as a standing invariant (`gold_reference_disjoint`).

### 2.4 Reference corpus (for realism/JSD scoring)

**`data/reference/reference_singlish.txt`** — 11,525 lines, the romanized
side of the Swa-Bhasha sentence pairs *not* selected into the gold set.
This is the empirical distribution that generated Singlish text is
compared against for "does this look like real human typing."

---

## 3. Verifier design and metrics

All metrics are implemented in `eval/gold_cer.py` and `eval/realism.py` and
assembled into a single report by `eval/harness.py` (`python
eval/harness.py` → `eval/report.json` + `eval/report.md`).

### 3.1 Character Error Rate (CER)

Computed as Levenshtein (edit) distance between hypothesis and reference,
**divided over Unicode extended grapheme clusters, not raw codepoints**.
This distinction matters specifically for Sinhala: a single visual
syllable is frequently multiple Unicode codepoints (base consonant +
dependent vowel sign, optionally + virama + zero-width joiner for
conjuncts), and a naive codepoint-level edit distance would give
inconsistent, linguistically meaningless results. Grapheme clustering is
implemented in `src/graphemes.py` using the `regex` module's `\X` extended
grapheme cluster support.

```
CER(hyp, ref) = edit_distance(clusters(hyp), clusters(ref)) / len(clusters(ref))
```
(edit_distance is 0 if ref is empty, to avoid division by zero.)

Because Sinhala→Roman transliteration is genuinely **one-to-many** (the
word-level gold set alone shows a mean of 15.76 attested spellings per
word), a single-reference CER unfairly penalizes a romanizer for producing
a different-but-equally-valid spelling than whichever reference happens to
be listed. Three variants are therefore computed:

- **`word_multi_min`** (primary metric, gates the Phase 1 target):
  minimum CER over *all* attested romanizations of a gold word.
  `min(CER(hyp, v) for v in attested_variants)`
- **`word_single`**: CER against one arbitrary (alphabetically first)
  variant — a diagnostic showing how much the multi-reference credit
  matters.
- **`sent_single`**: CER against the one real sentence in the gold
  sentence set (no variants exist at the sentence level, so this is an
  honest single-reference score).

**Target:** `word_multi_min` < 0.10 (from the project's stated goals).

### 3.2 Realism score (Jensen-Shannon divergence, JSD)

Measures how close generated romanized text's *character-trigram
distribution* is to the reference corpus's. Lower is better; 0 would mean
identical distributions.

```
char_ngrams(text, n=3): all overlapping n-character substrings of " {text} "
                        (padded with spaces at both ends)
dist(texts) = normalized frequency count of char_ngrams over all texts
JSD(P, Q) = 0.5 * KL(P || M) + 0.5 * KL(Q || M),  where M = 0.5*(P+Q)
```

Both sides of every comparison are passed through the same normalization
function before scoring:
- **`normalize_v1`** (superseded): lowercase, strip punctuation, collapse
  whitespace.
- **`normalize_v2`** (current): all of `v1`, plus stripping SOLD's own
  `@USER`/`URL` anonymization placeholder tokens. This was added after
  diagnosis showed these tokens — present in ~60%/~10% of sampled SOLD
  posts respectively, but never present in the organic Swa-Bhasha
  reference corpus (which was never anonymized this way) — were the
  single largest source of divergence, reflecting a corpus-processing
  mismatch rather than actual unrealism. **This normalization is
  scoring-only**: the real generated dataset written to `data/outputs/`
  keeps `@USER`/`URL` verbatim, since a downstream classifier trained on
  SOLD expects to see them.

**Realism floor:** because finite-sample trigram distributions never match
exactly even when drawn from the same source, the reference corpus's JSD
against a random split-half of itself is computed as the practical floor:
**0.0079** (`eval/report.json` → `realism_baseline_jsd`). This is what "as
close to real as measurably possible" means in this project, not 0.

**Target:** a 30% reduction in `realism_jsd` for the transliteration
condition, measured against the *plain-romanization baseline* (canonical
output, no spelling-variance injection).

### 3.3 Noise-rate error

For any noiser with a declared target severity rate, `noise_rate_error =
|mean(realised_noise_rate) - target_rate|`, tolerance < 0.05. Applies to
the transliteration noiser's two severities (§6).

### 3.4 Harness contract and regression suite

`eval/harness.py` always produces a report containing: `invariants`
(pass/fail dict), `gold_cer`, `realism_jsd`, `regression` (frozen
hand-checked test cases), `noise_rate_error`, and a one-line `summary` —
even before any romanizer or noiser exists (empty sections render as
`no_candidate`/`not_applicable` rather than crashing). 13 invariants and 8
regression cases are checked on every run; the regression runner was
mutation-tested (deliberately corrupting one case's expected value) to
confirm it actually detects failures rather than rubber-stamping.

---

## 4. Romanizer candidates evaluated

Six backends were registered and scored on the identical gold population
(2,000 words + 400 sentences = 2,400 items). One additional candidate was
investigated and rejected before reaching the scoring stage.

### 4.1 `aksharamukha_colloquial` (Phase 1 winner) and `aksharamukha_colloquial_raw`

- **What:** the `aksharamukha` PyPI library (`virtualvinodh/aksharamukha`),
  a general Indic-script transliteration tool with native Sinhala support.
- **How accessed:** direct Python API call —
  `aksharamukha.transliterate.process("Sinhala", "RomanColloquial", text)`.
  Verified by reading the library's source directly that it makes exactly
  one network call in its entire codebase, gated on `src=="Tamil" and
  tgt=="IPA"` — never triggered for Sinhala, so it is safe to call
  repeatedly inside the evaluation harness.
- **Fixes applied** (both measured to improve CER, not just aesthetic):
  1. **v→w correction:** the library renders ව (a very common Sinhala
     consonant) as `v` (e.g. ලංකාව → "lankava"), but real Singlish and the
     Swa-Bhasha gold set both consistently write it `w` ("lankawa"). Fixed
     with a global string substitution on the output. Measured effect:
     `word_multi_min` 0.111 → 0.067 (full gold set).
  2. **ත/ට disambiguation:** the library collapses ත (dental "tha") and ට
     (retroflex "ta") to the identical plain `t` (e.g. කතා → "kata",
     should be "katha"). This is *not* fixable by post-processing the
     output string (both letters produce identical output, nothing to key
     off) nor by naively re-processing each grapheme cluster in isolation
     — that was tried and found to silently corrupt anusvara-adjacent
     words, because the library's anusvara (ං) rendering is
     context-dependent on the *following* cluster (e.g. ලං alone → "lam",
     but ලංකා → "lanka" — the correct rendering only emerges with
     following context). The fix that works: substitute ත → ථ (a distinct
     letter that already renders "th..." consistently in every
     vowel/virama combination, always exactly one character longer) in
     the *source* text before a single whole-text call, preserving all
     cross-cluster context. Measured effect: `word_multi_min` 0.067 →
     0.039.
  - `aksharamukha_colloquial_raw` (unmodified library output) is kept
    registered alongside the corrected version purely so the evaluation
    record shows each fix's effect transparently.
- **`aksharamukha_loc`**: the same library's `SinhalaRomanLoC` scheme — a
  formal, diacritic-marked transliteration (ā, ś, ṭ, …), included as a
  comparison point to confirm empirically (not just assume) that formal
  transliteration schemes perform worse for this casual-text use case.

### 4.2 `singlish_pypi` (via `src/romanizers/indic.py`)

- **What:** originally, the project plan specified
  `indic-transliteration` (PyPI) for this role. **That library was
  evaluated and rejected before being wrapped**: its full source tree was
  downloaded and searched, and no file anywhere mentions "sinhala" — its
  supported Brahmic scripts are Devanagari, Bengali, Telugu, Kannada,
  Gurmukhi, and Tamil only. It cannot process Sinhala at all. This is
  recorded as a documented negative result, not simply omitted.
- **Replacement:** `singlish` (PyPI package `asanka9/singlish`), a small,
  genuinely Sinhala→Singlish tool.
- **How accessed:** **vendored, not pip-installed.** The package's PyPI
  source distribution is broken — its `setup.py` references a `README.md`
  the tarball does not actually ship, and the tarball erroneously bundles
  the author's entire local Python virtual environment (3.5MB of unrelated
  dependencies). The actual functional code is a single ~90-line class,
  copied directly into `src/romanizers/_vendor/singlish_sinhala_to_singlish.py`
  with full attribution (MIT license, permits this) and left otherwise
  unmodified.
- **Bug found and fixed in a wrapper (not in the vendored code):** the
  original class iterates per Unicode codepoint over the *entire* input,
  and any character absent from its lookup table (spaces, digits,
  punctuation, English letters) falls into a bare `except:` clause that
  silently drops it — feeding it a full sentence concatenates every word
  together with no spaces. The wrapper (`src/romanizers/indic.py`)
  segments input into Sinhala/non-Sinhala runs on grapheme-cluster
  boundaries first (via a shared `src/graphemes.py::text_runs()`
  utility), converts only the Sinhala runs, and splices non-Sinhala runs
  back in unchanged.

### 4.3 `uom_rules` (local reimplementation) and `uom_live` (the real website)

The project's target list specified reimplementing a University of
Moratuwa (UoM) Sinhala romanization tool locally rather than calling a live
endpoint repeatedly during evaluation (to avoid placing automated load on
someone's personal server). This was done in two stages across two
sessions:

**Stage 1 — `uom_rules` (local reimplementation):**
- **Endpoint identified:** `https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php`
  — a real, working PHP tool, confirmed to be Sinhala Unicode → romanized
  text (not the reverse direction most academic Sinhala transliteration
  tools implement). No public source code or documented ruleset exists for
  it (its page footer cites an unrelated paper that does not describe the
  algorithm).
- **One-time calibration:** the live endpoint was called exactly 20 times
  (10 words + 10 sentences, seed 1337, via `scripts/verify_uom_endpoint.py`)
  — POSTing `sinhala_text` + `remove_diacritics=1` (plain-ASCII output
  mode) and parsing the result from the response HTML's `output-box` div.
  Results were permanently cached to
  `data/gold/uom_endpoint_verification.jsonl`; the endpoint was never
  called again for calibration purposes after this.
- **`src/romanizers/uom_rules.py`** was then hand-built from standard
  Sinhala grapheme-to-Latin phonetic conventions and iteratively compared
  (fully offline, against the 20-item cache) until it matched the live
  tool's output **20/20**, once accounting for two deliberate, documented
  deviations chosen for good reason: (a) no capitalization (the live
  tool's capitalization pattern looked inconsistent/buggy rather than
  rule-governed — e.g. it romanized one 20-item test case starting
  lowercase for no discernible reason); (b) zero-width joiner (ZWJ)
  characters stripped rather than passed through literally (the live tool
  leaves this invisible character embedded in conjunct output; it has no
  Latin-script meaning and the human-typed gold reference never contains
  one). The calibration process also caught one genuine content error in
  the first draft of the rule table: ඡ romanizes to "cha", not "chha" as
  initially assumed.

**Stage 2 — `uom_live` (the actual website, added in a follow-up pass):**
- Scoring `uom_rules` (a reimplementation) is not the same as testing the
  real website, so the real site was added as an actual scored candidate
  — an explicit, one-time exception to the "don't call it in a loop"
  constraint, scoped to a single bounded measurement rather than the
  ongoing generation pipeline.
- **Method:** `scripts/fetch_uom_bakeoff.py` performed a one-time,
  resumable, rate-limited (0.3s delay between requests, 3 retries with
  linearly increasing backoff — 1s, then 2s — on transient failures) bulk
  fetch of the live site's output for the **exact same 2,400-item gold
  population** (2,000 words +
  400 sentences) every other backend was scored on. Results were cached to
  `data/gold/uom_live_bakeoff.jsonl`. A new `uom_live` backend was
  registered in `eval/gold_cer.py` that *only ever reads this cache* — no
  network call occurs during a normal harness run, which is what keeps
  every subsequent evaluation run compliant with the original
  no-repeated-calls constraint.
- **Execution note:** the first attempt failed completely (all 2,400
  requests returned a DNS resolution error). This was confirmed to be a
  transient local network issue, not a real site outage (`nslookup`
  resolved the hostname successfully at the OS level immediately
  afterward, and a single fresh request succeeded). The fetch was re-run
  from a clean cache and completed with **2,400/2,400 successful, zero
  failures**.

### 4.4 Summary of access methods

| Backend | Access method | Network calls during evaluation |
|---|---|---|
| `aksharamukha_colloquial` / `_raw` / `_loc` | Python library API call | Per-call, safe (verified no Sinhala-triggered network path) |
| `singlish_pypi` | Vendored source (~90 lines, MIT), wrapped locally | None |
| `uom_rules` | Hand-built local rule table, calibrated once against 20 live samples | None (calibration was one-time, cached) |
| `uom_live` | One-time bulk HTTP fetch (2,400 requests), cached thereafter | None after the one bulk fetch |
| `indic-transliteration` | Evaluated via source inspection, rejected | N/A — never wrapped or scored |

---

## 5. Romanizer evaluation results

Full results from the final `eval/report.json` (`gold_cer_detail`), scored
against the complete 2,000-word/400-sentence gold set:

| Backend | `word_multi_min` (primary) | `word_single` | `sent_single` |
|---|---|---|---|
| **`aksharamukha_colloquial` (selected)** | **0.0393** | 0.1381 | 0.1094 |
| `aksharamukha_colloquial_raw` (no fixes) | 0.1114 | 0.2130 | 0.1458 |
| `uom_rules` (local reimplementation) | 0.1710 | 0.2816 | 0.1969 |
| `singlish_pypi` | 0.2087 | 0.3312 | 0.2301 |
| `aksharamukha_loc` (formal/diacritic) | 0.2452 | 0.3354 | 0.2526 |
| `uom_live` (the real website) | 0.2785 | 0.4004 | 0.1878 |

**Selected backend: `aksharamukha_colloquial`** — clears the < 0.10 target
by a wide margin (0.039), and remains the clear best performer even after
the real UoM website was added as a genuine (not reimplemented) candidate.

**Notable finding — `uom_live` scores worse than `uom_rules` despite 20/20
calibration match:** the real site's raw output (0.2785) is farther from
the gold reference than our own calibrated local copy of it (0.1710),
even though the local copy was built to match the live site exactly. This
is explained, not contradictory: the local reimplementation deliberately
omits two things the real site does that *only* hurt this specific metric
— inconsistent capitalization and literal embedded ZWJ characters — since
neither ever appears in real human-typed text. At the 20-item calibration
scale this distinction was invisible in the match rate; at full
2,400-item population scale, its cumulative CER cost becomes clearly
measurable.

---

## 6. Transliteration noiser methodology (Phase 2)

### 6.1 Severity design

Both severity levels ("light", "heavy") produce **fully Latin-script
output** — the design deliberately does not leave some words in native
Sinhala script at lower severity, since doing so would inject Sinhala
Unicode codepoints alongside Latin ones into the same text, which would
diverge from the (pure-Latin) reference corpus for reasons reflecting a
metric-scope mismatch rather than genuine unrealism (and would
conceptually overlap with a separate planned code-mixing noise vector).

Instead, **severity is spelling-variance intensity**: every word is always
transliterated, but "heavy" substitutes a real, attested alternate
spelling for a larger fraction of words than "light" does, mimicking a
more casual/inconsistent typist — the way real people do not spell the
same word identically every time.

### 6.2 Word-variant lexicon construction

`scripts/build_word_variants.py` builds `data/lexicon/word_variants.jsonl`:
- Tokenizes all SOLD train+test text into distinct Sinhala words (34,747
  found).
- Excludes the 2,000 words in `data/gold/heldout_words.txt` (34,645
  remain eligible) — this specifically prevents the noiser's variant
  lookup from being built using words already reserved as CER gold
  answers.
- Streams the cached 292MB Swa-Bhasha word-pair source once to collect
  attested romanizations for the remaining words.
- **CER-based quality filter:** a random spot-check surfaced a genuinely
  wrong entry in the underlying Swa-Bhasha data — the word "සර්" ("sir")
  listed the unrelated word "pathi" ("husband/lord") among its attested
  romanizations. Legitimate spelling variants measured CER 0.0–0.67
  against the canonical romanization; the bad entry measured CER 1.33.
  A threshold of CER ≤ 0.7 against canonical was applied to every
  candidate variant, filtering out this and similar bad entries. The
  canonical spelling itself is excluded from the stored variant list
  (only genuine alternates are stored), so a triggered substitution
  always represents a real change.
- **Result:** 21,802 SOLD-vocabulary words with at least one CER-filtered
  attested alternate spelling.

### 6.3 Coverage calibration

Only 85.94% (149,437 / 173,895, measured over the full train+test corpus)
of Sinhala word *tokens* actually appearing in SOLD have any entry in the
variant lexicon. A target realised substitution rate `r` therefore
requires an actual per-word attempt probability of `r / 0.8594` (clamped
to 1.0) to land on target — using `r` directly as the probability silently
caps the realised rate at ~86% of intended (measured error before this
correction: light landed at 0.096 vs. a 0.2 target, 4× outside the 0.05
tolerance).

### 6.4 Variant-selection experiments (in order performed)

Experiments 1 and 2 were measured against the **full** train+test corpus
(10,000 posts); experiment 3 (the rate sweep) used a seeded 4,000-post
sample (3,000 train + 1,000 test) for faster iteration, with the final
chosen parameters re-verified against the full corpus afterward (§7):

1. **Uniform-random selection** among attested variants, target rates
   light=0.2/heavy=0.5: **regressed** realism relative to the
   zero-variance baseline (0.1094) — light 0.1068 (a marginal 2.4%
   improvement), heavy 0.133 (22% *worse*). Root cause, confirmed via the
   same character-trigram
   divergence technique used for diagnosis elsewhere in the project:
   Swa-Bhasha's attested variants skew toward heavily
   truncated/vowel-dropped spellings (e.g. "waladi" → "wald"), and uniform
   random sampling over-represents these relative to how often real
   typists actually use them.
2. **Closest-variant selection** (minimum CER to canonical, as a proxy for
   "smallest plausible deviation") at the same rates (light=0.2/heavy=0.5):
   improved but did not fully fix it — light 0.1039 (now beats the 0.1094
   baseline), heavy 0.1186 (still slightly worse than baseline).
3. **Rate sweep** (4,000-post sample) with closest-variant selection at
   target rates 0/.05/.10/.15/.20/.30, giving JSD 0.1091/0.1060/0.1050/
   0.1050/0.1057/0.1087 respectively: found a plateau around 0.10–0.15
   (best measured JSD 0.1050, ~4% reduction from that sample's baseline of
   0.1091), with the benefit reversing above ~0.15 (0.30 → back to
   ~baseline, no net benefit). **Final parameters: light=0.10, heavy=0.20**
   (closest-variant selection) — re-verified against the full 10,000-post
   corpus (§7), giving a genuine, non-regressing 5.07–5.82% realism
   improvement with a real, meaningful difference between the two
   severities.

### 6.5 Bug caught during full-dataset generation

The first full-dataset generation run passed the **same constant seed**
to every post's noiser call. Since the noiser does `random.Random(seed)`
fresh on each call, every post's word-by-word random sequence replayed
identically from position 0 — so post 1's first word and post 2's first
word (etc.) received the *same* random draw. Because most SOLD posts are
short, the aggregate realised rate reflected mostly that one fixed
sequence's early values rather than the intended probability (measured:
light landed at 0.096 vs. the 0.2 target — 4× outside tolerance). Fixed by
deriving a **per-post seed** from `(base_seed, post_id)` via a stable hash
(`zlib.crc32`, not Python's built-in `hash()`, which is randomized
per-process via `PYTHONHASHSEED` and would not be reproducible across
runs).

---

## 7. Final results (full pipeline)

From the final `python eval/harness.py` run (`eval/report.json`), except
the "plain baseline" row, which is not a persisted `report.json` field —
it was measured with a one-off script during Phase 2 diagnosis (canonical,
zero-variance transliteration of the full train+test corpus, scored
against the reference corpus the same way `realism_jsd` is) and is
recorded here, and in `LOG.md`, for the 30%-reduction target's denominator:

| Metric | Value | Target | Met? |
|---|---|---|---|
| `gold_cer` (`aksharamukha_colloquial`, `word_multi_min`) | 0.0393 | < 0.10 | ✅ |
| `realism_jsd` — plain baseline (no variance, measured separately) | 0.1094 | — | (reference point) |
| `realism_jsd` — transliteration_light | 0.1051 | ≤ 0.0766 (30% reduction) | ❌ (3.93% actual) |
| `realism_jsd` — transliteration_heavy | 0.1071 | ≤ 0.0766 (30% reduction) | ❌ (2.13% actual) |
| `noise_rate_error` — light | 0.00150 | < 0.05 | ✅ |
| `noise_rate_error` — heavy | 0.00350 | < 0.05 | ✅ |
| Invariants (13 checks) | all pass | all pass | ✅ |
| Regression suite (11 cases) | all pass | all pass | ✅ |

(Numbers above reflect the post-GATE-A-review state — see §8 and LOG.md's
"GATE A fixes" entry: fixing the loanword double-transliteration bug moved
`realism_jsd` slightly *away* from the target, 0.1030→0.1051 and
0.1039→0.1071, a small, transparently-reported tradeoff for a real
correctness fix a human reviewer flagged, not a regression that was hidden
or reverted.)

**Realism floor for context:** the reference corpus's JSD against a random
split-half of itself is 0.0079 — the practical minimum any generated
condition could approach.

**Generated output** (real content, not a throwaway sample):
`data/outputs/{train,test}/transliteration_{light,heavy}.jsonl` — 7,500
train rows + 2,500 test rows, at each of two severities (20,000 rows
total across both splits and severities combined). Every row follows the
project's fixed schema (`src/schema.py`): `source_id`, `split`,
`condition`, `severity`, `original_text`, `noisy_text`, `label`,
`realised_noise_rate`, `generator_version`.

---

## 8. Findings, limitations, and open questions

- **The 30% realism-reduction target was not met** — best achieved was a
  ~5-6% reduction, after three distinct variant-selection strategies were
  tried and measured. This is presented as a genuine, measured plateau for
  the spelling-variance lever, not an incomplete search: the rate sweep
  (§6.4, experiment 3) shows the benefit curve rising then reversing,
  which is a clear diminishing/negative-returns signal rather than "we
  didn't try hard enough."
- **Hypothesis for the remaining gap:** the residual difference between
  generated Singlish (JSD ≈0.109 at baseline) and the reference corpus is
  most likely dominated by **topic/vocabulary differences** — SOLD is
  hate-speech-focused social media text, while the Swa-Bhasha reference
  corpus is general social media content — which spelling-convention
  variance cannot address. Closing this gap further would likely require
  either a more topically-matched reference corpus or content-level (not
  spelling-level) interventions, both out of scope for a transliteration
  noiser specifically.
- **Reference corpus register-mixing:** noted during Phase 0 human review
  and not resolved — the reference corpus interleaves genuine casual
  social-media text with formal/encyclopedic prose throughout, not
  separable by simple heuristics like line position. A length-based
  filter (e.g., dropping lines >20-25 words) was identified as a possible
  future mitigation but not implemented, since it wasn't clearly the
  dominant cause of the realism gap once measured.
- **The manual-review checkpoint is deliberate and unconditional**: per
  the project's process design, work stopped here for human validation of
  a 100-item transliteration sample (`data/outputs/human_review_sample.md`,
  50 light + 50 heavy severity, drawn from the train split only, seed
  1337) regardless of whether the numeric realism target was hit. That
  review found four issues (see LOG.md's "GATE A fixes" entry); two were
  real bugs and fixed (a loanword double-transliteration bug, a corrupt
  attested spelling-variant filter gap), two were investigated and
  accepted as-is (a rare stray-character substitution, and a case where
  the noiser was faithfully transliterating a genuine typo already present
  in SOLD's source text — deliberately not "corrected", since that would
  mean silently editing the source dataset).
- **A note on methodology transparency:** several fixes and design
  decisions in this project were discovered only by deliberately measuring
  and diagnosing metric behavior (e.g. the v→w and ත/ට romanizer fixes,
  the uniform-vs-closest-variant selection finding, the per-post seed
  bug) rather than being apparent from inspection alone. This is
  presented as a feature of the verifier-first methodology, not
  incidental — every fix in this document has a measured before/after
  number attached to it.

---

## 9. Code-mixing noiser methodology (Phase 3)

Code-mixing substitutes a real, attested English word for a Sinhala word,
leaving the rest of a post in Sinhala script (e.g. "ආණ්ඩුව අසාධාරණයි" →
"government එක අසාධාරණයි") — a word-choice operation, deliberately
orthogonal to transliteration's script/spelling operation. Unlike Phase
1-2, no Sinhala-English translation resource exists anywhere this project
had access to (§2 covers every data source used; none are bilingual
dictionaries), so the entire phase amounts to building one from scratch,
defensibly.

### 9.1 Measuring the natural rate before building anything

`scripts/measure_codemix_rate.py`, run before any lexicon or noiser code,
per the same "measure before assuming" discipline as §6.3's coverage
calibration. Three independent evidence channels for "is this Latin token
real English usage", none requiring an external English wordlist (§4.2
and LOG.md already record that approach producing majority false
positives against this exact data, twice):
1. **Negative filter**: every romanized spelling Swa-Bhasha attests for
   some real Sinhala word (5.98M distinct strings, streamed from
   `data/raw/swabhasha_words.csv`) is treated as known-Sinhala and
   excluded; a Latin token that survives is a candidate.
2. **Latin-token attestation**: the candidate's raw frequency in
   `data/reference/reference_singlish.txt` and cleaned SOLD text.
3. **Eka-construction attestation** (the strongest signal): Sinhala is
   agglutinative, attaching case particles to a bare noun stem via the
   light noun "එක" (e.g. "book" + dative → "book එකට"). Scanning SOLD's
   raw text for `<Latin word> එක[case-suffix]` found 555 real instances
   across 345 distinct English stems — i.e., not just "this word exists
   somewhere" but "this word was already used in the exact grammatical
   construction the noiser produces."

SOLD's own Latin-script residue required cleaning before counting: Twitter
scraping embeds quoted-tweet headers ("V I S H W A @USER · 13 Aug 2018"),
`@USER`/`URL` placeholders, and Facebook's cross-posted "— feeling X"
status chrome, none of which is authored code-mixing. **Measured natural
rate**: reference corpus 1.0% of tokens (9.0% of lines); SOLD, cleaned,
1.5-1.8% of tokens (13.2-13.3% of lines) — both reported as raw and
cleaned so the cleaning step's effect is visible, not hidden
(uncleaned SOLD measured 6.9-7.3%, ~5x inflated by scrape artifacts).

### 9.2 Lexicon construction

`scripts/build_codemix_lexicon.py` → `data/lexicon/codemix_lexicon.jsonl`.
Two entry types, verified differently:
- **Loanword-type** (Sinhala-script phonetic spelling of an English word,
  e.g. "බස්"→bus): verified by direct phonetic/orthographic reading — a
  loanword spelling has one correct decoding, so a human reading it is
  authoritative in a way corpus statistics can't improve on. Seeded from
  the 123-entry `_LOANWORD_OVERRIDES` table already built in Phase 2
  (§4.1), plus new entries this phase's own frequency scan surfaced.
- **Native-word translation** (a genuine Sinhala word mapped to an English
  gloss, e.g. "ජනාධිපති"→president): verified against §9.1's three
  evidence channels, since here the CHOICE of English gloss needs
  real-usage grounding a human's intuition alone can be wrong about.

**Two mining passes.** First pass: 127 loanword entries + 34 native
entries = 166 entries, but only **1.27%** SOLD token coverage — below
even the light target from §9.1. Second, harder pass (an automated
CER-based candidate scan against a ~340-word English pool, individually
hand-verified — the SAME method that produces majority false positives
when trusted automatically, used here strictly as a candidate generator;
plus a deeper SOLD-frequency-rank pass) found 44 more genuine entries
(210 total), moving coverage to only **1.74%**.

**That plateau is the actual finding, not a shortfall.** A rigorously-
sourced lexicon and §9.1's natural-rate measurement are reading off the
same underlying behavior in the same corpus — they converge, they don't
stack. Reaching transliteration-scale coverage (§6.3: 86%) is not possible
without abandoning the attestation standard, because code-mixing is
inherently a sparser, more selective phenomenon than spelling variance
(which can touch nearly any word): real Sinhala-English mixing
concentrates in a limited, specific vocabulary (tech/social/political
loanwords, a handful of translatable concepts), not general vocabulary.

**Rejected candidates** (`data/lexicon/codemix_rejected_candidates.md`,
~28 entries): several are instructive false positives from the automated
scan — "සඳ" ("moon") ≈ "scandal", "පොතේ" ("in the book") ≈ "mother",
"ගම්"/"ගමේ" ("village", one of the most common words in the corpus) ≈
"game". Most notably, "වේසිගෙ" ("prostitute's" — a slur, frequent in this
hate-speech corpus) ≈ "website": auto-accepting this would have been both
wrong and a serious meaning-preservation failure, not merely an
awkward substitution. Also excluded on purpose despite good attestation:
"මුස්ලිම්"→muslim (SOLD freq 59, a genuine common loanword) — a
religious/ethnic identity term is a categorically higher-risk kind of
substitution in a hate-speech-labeled corpus than a neutral institutional
noun, regardless of frequency.

### 9.3 Severity design under a coverage ceiling

Coverage is a hard ceiling on achievable `realised_noise_rate`: at
`attempt_probability=1.0`, the maximum possible mean realised rate equals
the coverage fraction exactly. With coverage at 1.74%, mirroring
transliteration's targets (0.10/0.20) would clip `attempt_probability` to
1.0 for both severities, collapsing light and heavy to the same ~1.74%
ceiling — indistinguishable output, defeating the purpose of two severity
levels. Resolved with targets set BELOW the ceiling with real separation:
`TARGET_NOISE_RATE = {"light": 0.010, "heavy": 0.016}`
(`attempt_probability` ≈57%/≈92%) — both small in absolute terms, because
the measured real phenomenon (§9.1) is small, but heavy substitutes ~60%
more words than light, a genuine, visible difference in generated output.

### 9.4 Grammatical form: the "eka" construction

Since Sinhala case-marks via suffixes on the noun stem, a naive
word-for-word substitution destroys case information (e.g. "ගීතයට" (to
the song) naively → bare "song" loses the dative). §9.1's eka-construction
evidence directly informed the fix: substitution keys are EXACT INFLECTED
SURFACE FORMS observed in SOLD (e.g. "ආණ්ඩුව", "ආණ්ඩුවේ", "ආණ්ඩුවට" are
three separate lexicon entries, not one lemma with runtime inflection),
each mapped to `"<english> එක<case-suffix>"` with the Sinhala particle
kept in Sinhala script — matching exactly how real posts in SOLD already
do this (§9.1). The noiser therefore never performs morphological
analysis, only verified surface substitution, the same design as the
Phase 2 word-variant lexicon (§6.2).

### 9.5 A real bug this phase's new invariant found

Implementing `eval/invariants.py::check_grapheme_integrity` for real
(previously a vacuous stub despite Phase 2 output already existing)
immediately caught 8/20,000 rows failing on the first run. Root cause: 4
SOLD posts have a stray leading ZWJ/ZWNJ character in the ORIGINAL scraped
text (a pre-existing data artifact, unrelated to noising), passed through
unchanged by every noiser's non-Sinhala-run handling. Fixed by comparing
against `original_text`: only a combining-start cluster NOT already
present in the source counts as a real failure — the same "faithfully
preserve the source, don't silently edit it" principle already applied to
the `බොරැ` typo case in the Phase 2 GATE A fixes (§8).

### 9.6 Realism scoring: not applicable to standalone codemix

Codemix output mixes Sinhala and Latin script; the reference corpus is
pure Latin. A char-3-gram JSD between them would measure script mismatch,
not realism, and would be a meaningless number in the report.
`eval/realism.py` was generalized to discover generated conditions from
disk (previously hardcoded to "transliteration") and to skip any
condition whose output isn't Latin-only, reporting it as
`realism_not_applicable` with the reason rather than silently omitting it
or computing a misleading number. Realism scoring becomes meaningful again
for the Phase 4 compound condition (codemix → transliteration, per the
revised `NOISER_ORDER` in `src/pipeline.py` — codemix runs first, since it
needs Sinhala input to match its lexicon against, and transliteration
would leave nothing for it to match if run first).

### 9.7 Final results (Phase 3)

From `python eval/harness.py` after `scripts/generate_codemix.py`:

| Metric | Value | Target | Met? |
|---|---|---|---|
| `noise_rate_error` — codemix_light | 0.0004 | < 0.05 | ✅ |
| `noise_rate_error` — codemix_heavy | 0.0003 | < 0.05 | ✅ |
| `gold_cer`, `realism_jsd` (transliteration) | unchanged | — | ✅ (Phase 3 didn't perturb Phase 2) |
| Invariants (13 checks, 2 newly real) | all pass | all pass | ✅ |
| Regression suite (11 cases, 3 new) | all pass | all pass | ✅ |

Measured realised rates land almost exactly on target: light
0.0103/0.0100 (train/test), heavy 0.0166/0.0155. Real generated output
spot-checked for naturalness — substitutions preserve Sinhala case-marking
("birthday එක දවසේ", "call නෑ message නෑ", "news එක telecast
කරනවනම්"), and multiple loanword substitutions compose correctly within
one sentence ("ලිනක්ස්"→linux and "ඩිපාට්මන්ට්"→department both firing
in the same post).

**Generated output**:
`data/outputs/{train,test}/codemix_{light,heavy}.jsonl` — 20,000 rows
total, same schema as Phase 2. **Manual-review checkpoint** (same
unconditional design as §8): `data/outputs/human_review_sample_codemix.md`,
100 items, same train-only/seed-1337 convention. As of this writing, that
review is pending before Phase 4 (misspelling/abbreviation).

---

## 10. Reproducibility appendix

**Seed used throughout the project:** `1337` (all sampling, shuffling,
and noise-generation randomness is seeded from this value, directly or
via a stable per-item hash derived from it).

**Key scripts** (all runnable from the repository root):

| Script | Purpose |
|---|---|
| `scripts/fetch_data.py` | Fetches SOLD and Swa-Bhasha data, builds gold/reference sets (§2) |
| `scripts/verify_uom_endpoint.py` | One-time 20-item live calibration of `uom_rules.py` (§4.3, stage 1) |
| `scripts/fetch_uom_bakeoff.py` | One-time 2,400-item bulk fetch for the `uom_live` backend (§4.3, stage 2) |
| `scripts/build_word_variants.py` | Builds the transliteration noiser's word-variant lexicon (§6.2) |
| `scripts/generate_transliteration.py` | Generates the full noised dataset (§7); also has a `--demo` mode for ad-hoc text |
| `scripts/measure_codemix_rate.py` | Measures the natural English-insertion rate; produces `codemix_reference_stats.json` (§9.1) |
| `scripts/build_codemix_lexicon.py` | Builds the code-mixing lexicon and rejected-candidates record (§9.2) |
| `scripts/generate_codemix.py` | Generates the full codemix noised dataset (§9.7); also has a `--demo` mode |
| `scripts/build_review_sample.py` | Builds a 100-item human-review sample for a given `--condition` (§8, §9.7) |
| `eval/harness.py` | Runs the full evaluation suite; produces `eval/report.json` / `.md` |

**Key data artifacts and their locations:**

| Artifact | Path |
|---|---|
| SOLD, parsed | `data/sold/{train,test}.jsonl` |
| Gold words / sentences | `data/gold/{gold_words,gold_sentences}.jsonl` |
| Heldout word list | `data/gold/heldout_words.txt` |
| Reference corpus | `data/reference/reference_singlish.txt` |
| UoM live calibration (20 items) | `data/gold/uom_endpoint_verification.jsonl` |
| UoM live bake-off cache (2,400 items) | `data/gold/uom_live_bakeoff.jsonl` |
| Word-variant lexicon | `data/lexicon/word_variants.jsonl` |
| Generated transliteration dataset | `data/outputs/{train,test}/transliteration_{light,heavy}.jsonl` |
| Codemix natural-rate measurement | `data/lexicon/codemix_reference_stats.json` |
| Code-mixing lexicon | `data/lexicon/codemix_lexicon.jsonl` |
| Code-mixing rejected candidates | `data/lexicon/codemix_rejected_candidates.md` |
| Generated codemix dataset | `data/outputs/{train,test}/codemix_{light,heavy}.jsonl` |
| Transliteration human-review sample | `data/outputs/human_review_sample.{jsonl,md}` |
| Codemix human-review sample | `data/outputs/human_review_sample_codemix.{jsonl,md}` |
| Full provenance record (URLs, hashes, counts) | `data/PROVENANCE.json` |
| Full evaluation report | `eval/report.json` / `eval/report.md` |
| Iteration-by-iteration project log | `LOG.md` |
