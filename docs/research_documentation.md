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

This section covers two designs. **v1** (§9.1-9.2) built a small,
rigorously-attested 210-entry lexicon and applied it probabilistically,
word by word. It worked, but coverage was low enough (1.74% of Sinhala
tokens) that most generated rows came out untouched. **v2** (§9.3
onward) replaced the selection mechanism entirely — forced per-post
substitution against a much larger, LLM-translated word bank, closed out
by three rounds of human review covering every entry that actually fired.
v1's lexicon and its "eka"-construction finding (§9.5) both survive
unchanged inside v2, at the highest precedence in the merged word bank.

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

**This 210-entry lexicon was not discarded when v2 replaced the selection
mechanism (§9.3-9.4) — it persists unchanged, at the highest
machine-verification precedence, inside the final 4,118-entry word bank.**

### 9.3 v1's ceiling, and why it was replaced

v1 applied the 210-entry lexicon probabilistically: each Sinhala word with
a lexicon entry was substituted independently with probability
`target_rate / coverage`. This produced a real measured problem — because
coverage (1.74% of tokens) is a hard ceiling on achievable
`realised_noise_rate`, and because substitution was decided per word
rather than per post, **85.8%/79.7% of light/heavy generated rows came
back byte-identical to their source**. Only 21.8% of posts contained any
word the lexicon could match at all; even among those, the probabilistic
draw skipped most of them. A "code-mixing noiser" that leaves 4 in 5 rows
untouched fails the benchmarking purpose of the dataset, independent of
how carefully each individual substitution was verified.

The fix required abandoning probabilistic selection, which in turn
required a much larger lexicon than 210 hand-verifiable entries — hence
v2 below.

### 9.4 v2 architecture: forced per-post selection, on-demand translation

**Selection.** For every post, `src/noisers/codemix.py::_apply()` forces
exactly 1 (light) or 2 (heavy) distinct word-bank-eligible word TYPES to
be substituted, capped at however many are actually present (never an
error to have fewer). Selection prefers word bank entries flagged
`codemix_plausible=true`, falling back to the full eligible pool only when
nothing plausible is available — trading some naturalness for coverage
rather than leaving a post untouched. `sorted()` before
`random.Random(seed).sample(...)` is load-bearing: Python randomizes `str`
hashing per process, so sampling from an unsorted set would silently
differ across separate runs of the same `(text, severity, seed)` — a
failure mode `check_determinism`'s single-process comparison cannot catch,
verified separately here by running generation twice in two OS processes
and diffing byte-for-byte.

**The word bank this needed** (`data/lexicon/codemix_wordbank.jsonl`) is
far larger than 210 entries: **4,118 entries** in the final build,
assembled by `scripts/build_codemix_wordbank.py` from four sources in
precedence order (each overrides the last on a conflict):
1. The original 210-entry v1 lexicon (§9.2) — unchanged, `source: native`/`loanword`.
2. 291 additional entries from an earlier, never-merged candidate-review
   pass (`data/lexicon/codemix_candidates_review.csv`).
3. **3,699 machine translations**, produced once, offline, via the
   Anthropic Message Batches API (`claude-opus-5`) —
   `scripts/select_codemix_targets.py` picked the top-4-by-frequency
   candidate words per post (7,969 unique types, reaching 9,934/10,000
   posts), `scripts/translate_codemix_worklist.py` translated the 7,638 of
   those not already covered by sources 1-2 (3,939 rejected by the model
   itself as untranslatable — mostly verb inflections and discourse
   particles the candidate filter didn't catch), each carrying a
   `codemix_plausible` judgment.
4. **992 human review corrections** (§9.7) — always highest precedence.

**Why this stays deterministic despite an LLM translating most of the
bank**: translation happens exactly once, offline, before generation ever
runs, and its output is frozen to disk. `_apply()` is a pure function of
`(text, severity, seed, the frozen word bank file)` — no network call
happens at generation time. `GENERATOR_VERSION` is stamped with the word
bank's own SHA-256 (first 8 hex chars) specifically so a bank rebuild is
always visible per output row even though the bank itself isn't part of
the noiser's own function signature.

**`TARGET_NOISE_RATE` changed roles.** Under forced selection, the
realised rate is a *consequence* of post length (more Sinhala words in a
post → a smaller fraction altered by the same fixed substitution count),
not something the noiser tunes toward — so it's demoted from a design
target to a drift tripwire: measured once from a completed generation run
and hard-coded, so `eval/harness.py`'s `noise_rate_error` can catch
unintended drift (a corrupted word bank, a corpus change) without implying
a natural-rate claim. The actual design spec (1/2 substitutions, capped at
availability, prefer-plausible) is checked directly by a new invariant,
`check_codemix_substitution_spec`, which independently re-derives the
eligible/plausible pool from the frozen bank for every persisted row
(rather than re-calling `_apply()` and trivially agreeing with itself).

### 9.5 Grammatical form: the "eka" construction

Unchanged from v1, and still central to v2. Since Sinhala case-marks via
suffixes on the noun stem, a naive word-for-word substitution destroys
case information (e.g. "ගීතයට" (to the song) naively → bare "song" loses
the dative). §9.1's eka-construction evidence directly informed the
fix, applied identically whether an entry is hand-verified or
LLM-translated: substitution keys are EXACT INFLECTED SURFACE FORMS
observed in SOLD (e.g. "ආණ්ඩුව", "ආණ්ඩුවේ", "ආණ්ඩුවට" are three separate
word bank entries, not one lemma with runtime inflection), each mapped to
`"<english> එක<case-suffix>"` with the Sinhala particle kept in Sinhala
script. The noiser never performs morphological analysis, only verified
surface substitution — the same design as the Phase 2 word-variant lexicon
(§6.2). This pattern turned out to be the single most common thing the
LLM translator got wrong (dropping the particle entirely, e.g. `තීරණයක්`
→ bare `decision` instead of `decision එකක්`), and so is also the
dominant category in the human review corrections (§9.7).

### 9.6 A real bug this phase's new invariant found

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

### 9.7 Three-round human review

`scripts/build_codemix_usage_report.py` produces
`data/lexicon/codemix_usage_review.{csv,md}` — not the full 4,200-entry
pre-correction word bank, but only the entries that **actually fired**
during generation (3,136 of them, originally), impact-ordered by how many
posts they touched. This inverted the review burden from v1-era planning
(a 12,000-row blind candidate list) to a bounded, priority-ordered list
where the top ~100 entries cover the large majority of all substitutions
in the corpus.

The user reviewed the entire document by hand across three rounds
(2026-08-13 to 2026-08-14, covering editor lines 1-3135 — every entry),
returning corrections in a Sinhala-English-mixed shorthand (e.g. "503
should be joke ekak", "488 removed due to ambiguity"). Two mechanics
worth recording:
- **The review's line numbers were raw editor line numbers, not the
  document's own `## N.` entry numbers** — the two schemes diverge because
  each entry spans a variable number of lines. Caught in round 1 by
  cross-checking distinctive corrections against actual word bank content
  before trusting either numbering (e.g. entry #827's `ආප්ප` was
  mistranslated "app" when it means the food "hoppers" — the user's
  correction "827. hoppers" only makes sense under the entry-number
  reading).
- **Corrections were durably recorded**, not applied as one-off edits:
  `data/lexicon/codemix_review_corrections.jsonl` is an append-only log
  (`{sinhala, action: "correct"|"remove", english, note}`) loaded by
  `build_codemix_wordbank.py` as the highest-precedence source, so the
  same rebuild mechanism served all three rounds with no new tooling.

**Final tally: 992 corrections — 910 corrected, 82 removed** — dropping
the word bank from 4,200 to **4,118 entries**. The dominant pattern
(~80% of corrections) was the missing eka-construction particle (§9.5);
the remainder split between genuine mistranslation fixes (e.g. `මැරියන්`
translated as the name "Marian" should be "die"; `කන්කජුලේසන්`
translated "concentration" is actually a phonetic rendering of
"congratulations") and removals of genuinely ambiguous words (e.g. `ඉඩ` =
space/room/chance/opportunity, no single safe target) or ones the LLM's
literal translation was wrong for with no clean fix (a handful of slurs
and near-slurs that slipped past the automated filter).

### 9.8 Realism scoring: not applicable to standalone codemix

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
needs Sinhala input to match its word bank against, and transliteration
would leave nothing for it to match if run first).

### 9.9 Final results (Phase 3, v2)

From `python eval/harness.py --strict` after the final (post-review)
`scripts/build_codemix_wordbank.py` → `scripts/generate_codemix.py`:

| Metric | Value | Target | Met? |
|---|---|---|---|
| Rows touched (train, light/heavy) | 93.2% / 93.2% | — | up from v1's 14.2%/20.3% |
| Rows touched (test, light/heavy) | 93.9% / 93.9% | — | up from v1's 14.2%/20.4% |
| Mean `realised_noise_rate` — light (train/test) | 0.0886 / 0.0876 | tripwire only | ✅ |
| Mean `realised_noise_rate` — heavy (train/test) | 0.1321 / 0.1306 | tripwire only | ✅ |
| `noise_rate_error` — codemix_light | 0.00005 | < 0.05 | ✅ |
| `noise_rate_error` — codemix_heavy | 0.00001 | < 0.05 | ✅ |
| `gold_cer`, `realism_jsd` (transliteration) | unchanged | — | ✅ (Phase 3 didn't perturb Phase 1-2) |
| Invariants (14 checks, incl. new `check_codemix_substitution_spec`) | all pass | all pass | ✅ |
| Regression suite (13 cases) | all pass | all pass | ✅ |

Word bank: **4,118 entries** (sha256 `e3c5381c...`) — 501 human-verified
(v1 lexicon + candidate-review pass) + 3,699 LLM-translated, less 82
entries removed by human review, with 910 more corrected in place. 93.2%
of train posts and 93.9% of test posts had at least one eligible,
translated word and were touched — the residual ~6-7% genuinely lack any
word bank match, a real ceiling (measured directly: 9,934/10,000 posts
have *some* candidate word, but not all of those got a usable
translation), not a bug.

Real generated output spot-checked for naturalness across all three
review rounds — substitutions read like plausible code-switching in the
large majority of cases (`madam`, `shop එකේ`, `court එකට`, `chance`,
`police officer කෙනෙක්`), with the human review pass catching and fixing
the minority that didn't (particle errors, outright mistranslations,
genuinely ambiguous words removed outright).

**Generated output**: `data/outputs/{train,test}/codemix_{light,heavy}.jsonl`
— 20,000 rows total, same schema as Phase 2 plus one additive field,
`n_substitutions` (count of distinct word types substituted). **Review
artifacts**: `data/lexicon/codemix_usage_review.{csv,md}` (impact-ordered,
post-correction snapshot) and
`data/outputs/human_review_sample_codemix{,_changed_only}.{jsonl,md}`
(100-item samples, train-only, seed 1337). The human-review gate for
Phase 3 is **closed** as of this writing — see `LOG.md` for the full
iteration-by-iteration record, including the real bugs found and fixed
along the way (a slur-filter import pointing at the wrong module, two
particle-romanization errors, an incomplete trailing-token parser).

---

## 11. Misspelling noiser methodology (Phase 4a)

The third noise vector: realistic Sinhala/Singlish typos, as opposed to
transliteration's spelling-variance (§6) or codemix's word-choice
substitution (§9). Two script-aware channels, dispatched per
grapheme-cluster run.

### 11.1 The mechanism: IME phonetic collision, not key adjacency

Most Sinhala text today is typed through a phonetic IME on an English
keyboard (Helakuru, Google Sinhala Input): the typist types a roman
spelling and the keyboard resolves it to a Sinhala grapheme cluster.
Where that roman→Sinhala mapping is genuinely ambiguous, the IME's choice
is sometimes not the one intended — type "na" and receive න when ණ was
meant. Two Sinhala grapheme clusters are therefore treated as
IME-confusable exactly when they romanize to the SAME string under the
Phase-1-winning backend (`romanize_colloquial`) — derived from SOLD
itself (`scripts/build_misspell_confusions.py`), the same
"measure, don't hand-guess" discipline §6.3 and §9.1 both established.

Measured over SOLD train+test: 767 distinct grapheme clusters observed,
grouped by romanization into **130 confusion sets** after dropping
clusters occurring fewer than 5 times and any cluster containing a
ZWJ/ZWNJ encoding artifact — covering **90.0%** of Sinhala cluster
tokens in the corpus. Unlike codemix v1's 1.74% lexicon-coverage
ceiling (§9.2), there is no coverage problem here: **99.4%** of Sinhala
word *tokens* contain at least one confusable cluster.

The sets land on textbook Sinhala orthographic confusions — nasal
quality (න/ණ), lateral quality (ල/ළ), dental-vs-retroflex (ත/ථ/ඨ),
consonant quality (ද/ඩ, ස/ශ/ෂ), and vowel length (e.g. "na" →
[න, නා, නැ, ණ, ණා]) — not noise, confirmed both by inspection and by
the human review round (§11.3).

### 11.2 Two channels

**Channel A (Sinhala script)**: one grapheme cluster swapped for another
member of its confusion set — always exactly 1-for-1, so cluster count
is structurally preserved (never checked after the fact and hoped for;
guaranteed by construction). Candidate selection is **prefer attested,
allow unattested**: a candidate is preferred if the resulting word form
appears in `data/lexicon/misspell_attested_vocab.txt` (SOLD's own
vocabulary unioned with the ~451K distinct Sinhala words in the
Swa-Bhasha word list — the same raw source §6.2's word-variant lexicon
draws from), falling back to the full confusion set only when nothing
attested is available. This mirrors codemix v2's `codemix_plausible`
prefer/fallback shape (§9.4) — attested-only would cap coverage at ~25%
of SOLD word types, and a typo is often, definitionally, not a real word.

**Channel B (Latin/Singlish script)**: rule-based, not lexicon-based —
geminate consonant drop/add, vowel length, aspiration, sibilant, w/v
swap, final -e/-a, and a deliberately low-weight QWERTY-adjacent slip.
This channel exists for correctness once misspell runs after
transliteration in the compound pipeline (`src/pipeline.py`'s
`NOISER_ORDER`), but is **not exercised by Phase 4a's own generation** —
the standalone `misspell` condition's input is always clean Sinhala SOLD
text, so Channel B only ever fires on pre-existing Latin content already
sitting inside a post (left unprotected deliberately: a realistic
misspelled variant of a mixed-script post plausibly misspells the Latin
portions too).

**Orthogonality rule (load-bearing):** any Latin form appearing in
`data/lexicon/word_variants.jsonl`'s attested romanizations is
transliteration's territory, not misspelling's — Channel B excludes every
candidate that lands on one of those forms. Without this, the two noise
vectors would silently measure the same underlying phenomenon under two
different names.

### 11.3 Human review

Single round (unlike codemix's three), reflecting a smaller, cleaner
derivation needing less correction: 130 confusion sets, impact-ordered by
corpus-token reach, reviewed against
`data/lexicon/misspell_confusions_review.md` (each set shown with real
before/after SOLD examples and an attested/unattested flag). **Result:
approved as-is, zero corrections.** One cosmetic oddity was flagged and
left in place as immaterial: one confusion set contained a visually
duplicate-looking cluster that turned out to be a malformed vowel-sign
encoding already present in SOLD's raw scraped text (frequency 7 of
30,986 tokens the set touches) — the same class of pre-existing
scrape artifact §9's slur/particle findings and the grapheme-integrity
check (§9.6-equivalent) already establish this project treats as
inherited, not introduced.

### 11.4 Severity and final results

Per-word attempt probability, coverage-corrected exactly like §6.3's
transliteration mechanism: `probability = target_rate / coverage`, with
`coverage = 0.9942` measured once over SOLD (fraction of Sinhala word
tokens with ≥1 confusable cluster). `TARGET_NOISE_RATE = {light: 0.05,
heavy: 0.15}` — deliberately below transliteration's 0.10/0.20, since
over-noising damages intelligibility more here (a misspelled word can
become unreadable; a code-mixed word is still a real word).

| Metric | light | heavy |
|---|---|---|
| `TARGET_NOISE_RATE` | 0.05 | 0.15 |
| Measured `realised_noise_rate` (pooled train+test) | ~0.0453 | ~0.1335 |
| `noise_rate_error` | 0.00576 | 0.01702 |
| Rows touched (≥1 word altered) | ~54% | ~83% |

Both severities landed within the 0.05 tolerance on the first generation
run — no recalibration needed, unlike transliteration's coverage-correction
discovery (§6.3) or codemix's rate redesign (§9.3-9.4).

**New invariant**: `check_misspell_substitution_spec` independently
re-derives structure from `(original_text, noisy_text)` rather than
trusting the noiser's own logic (the same discipline
`check_codemix_substitution_spec` established, §9.6) — for every changed
word it verifies exactly one cluster changed, cluster count and
ZWJ/ZWNJ-freedom are preserved, the new cluster is an actual member of
the old cluster's frozen confusion set (Channel A) or absent from the
attested-variants exclusion set (Channel B), and the row's
`realised_noise_rate` matches a from-scratch recomputation. **Result over
all 20,000 generated rows: zero violations.**

Full harness: **15/15 invariants, 17/17 regression (13 carried forward +
4 new misspell cases)**, `status: PASS`.

**Generated output**: `data/outputs/{train,test}/misspell_{light,heavy}.jsonl`
— 20,000 rows, same schema as Phases 2-3. **Review artifacts**:
`data/lexicon/misspell_confusions_review.{csv,md}` (impact-ordered,
post-review snapshot — approved as-is) and
`data/outputs/human_review_sample_misspell{,_changed_only}.{jsonl,md}`
(100-item samples, train-only, seed 1337).

---

## 13. Abbreviation noiser methodology (Phase 4b)

The fourth and final individual noise vector. Unlike the other three, this
one changed shape mid-implementation based on direct user review — the
original two-channel design collapsed to one, and the surviving channel's
own scope was pinned down in several rounds of iterative review. Both
changes are documented here in full rather than smoothed over, since the
process is as informative as the result.

### 13.1 Original design: two channels, one dropped

The initial plan mirrored misspelling's shape: a **Channel A** (single-word
clipping — a word losing a trailing syllable, e.g. an agglutinative suffix
drop) mined by requiring an exact grapheme-cluster prefix match on all but
a candidate's last cluster, then bounding only that cluster's edit distance
against the original word's remaining tail (reusing
`eval.gold_cer.edit_distance`, no new distance code). This single rule
captured both pure truncation and final-syllable fusion at once. Measured
at `FREQ_FLOOR=15`: 504 high-confidence (tail-distance-1) candidate pairs,
spot-checked as genuine colloquial suffix-drops, plus a much noisier
5,456-pair tier-2 tail dropped down to its top 150 highest-impact entries
for review-burden reasons.

**The user's review verdict was unambiguous: "total garbage... i dont
think that would be a good pathway to abbreviate."** Channel A —
`scripts/build_abbreviate_clippings.py` and every
`data/lexicon/abbreviate_clippings*` artifact — was removed from the repo
entirely, not merely deprioritized. This is recorded here specifically
because it's a case where a linguistically-motivated, empirically-tested
mining approach still failed the "would a real person type this" bar on
direct human judgment — the mechanical rigor of the derivation didn't
substitute for that judgment.

### 13.2 Channel B: phrase initialism — the surviving mechanism

The second channel, **phrase initialism**, collapses an approved two-word
Sinhala phrase to its first grapheme clusters, e.g. a phrase → `"X. Y."`.
This exists because the user identified a real, project-relevant pattern
the clipping mechanism could never produce: casual Sinhala texting
abbreviates **offensive multi-word phrases** to their initials, directly
useful for a pipeline whose entire purpose is benchmarking a hate-speech
classifier's robustness to realistic noise (§1) — an evasively-abbreviated
slur is exactly the kind of noise such a classifier needs to be tested
against, and SOLD's own labels are preserved untouched (inherited from
source, never recomputed), so this transforms already-labeled text rather
than inventing new offensive content.

**Corpus-grounded candidate surfacing.** `scripts/build_abbreviate_initialisms.py`
mines every Sinhala word bigram occurring back-to-back (whitespace-only
between the two words, no intervening punctuation) in SOLD at
`freq >= 8`, computing each one's OFF-label association rate (fraction of
its occurrences sitting in an OFF-labeled post) alongside raw frequency —
purely from SOLD's own statistics, no hand-listed slurs. 524 candidates
surfaced; 59 were >85% OFF-associated, a corpus-grounded, reviewable signal
for "this pair co-occurs almost exclusively in offensive posts."

**Opt-in, unlike every other lexicon in this project.** Every prior
lexicon (word variants, codemix's word bank, misspelling's confusion sets)
defaults to "accept unless a human rejects it." Channel B inverts that:
nothing enters the frozen `data/lexicon/abbreviate_initialisms.jsonl`
without an explicit `approve_bigram` correction — an unreviewed or
rejected candidate is simply absent. Chosen because this is the one
mechanism in the whole project whose highest-value use case is modeling
evasive obscenity, warranting a more conservative default than anywhere
else in the pipeline.

### 13.3 Review process

Three rounds, driven entirely by direct user requests rather than a
pre-planned rubric:

1. **Structural filter — single-character words.** User: drop any bigram
   where at least one word is a single Sinhala grapheme cluster (too
   degenerate to abbreviate meaningfully). 524 → 400 candidates. Presented
   as a clean word-only list (no example sentences, per explicit request,
   for faster scanning), split into "high offensive-association" and
   "general" tables — directly actionable for the user's stated priority
   of surfacing hate-speech word pairs.
2. **Structural filters — degenerate initials.** User: drop pairs where the
   same word repeats twice, and pairs where two *different* words happen to
   share the same first cluster (would abbreviate to a repeated-letter
   pattern like "P. P.", which doesn't read as a real initialism). 400 →
   378 candidates (8 + 14 dropped).
3. **Audit and sign-off.** Full removed-pairs list produced across all
   three exclusion reasons for a final check; confirmed correct ("okay. go
   ahead."). All 378 remaining candidates approved and frozen — sha256
   `2766d949...`.

**A fourth, post-generation check surfaced one more finding.** Reading the
100-item generation sample (§13.5) in full sentence context — something
the word-pair-only review rounds structurally couldn't see — revealed that
a meaningful share of the 378 approved bigrams are common grammatical
collocations (modal/auxiliary constructions, case-marked noun phrases)
rather than genuine recognizable fixed phrases, so their initialism reads
as confusing truncation rather than a natural shorthand in those cases —
even though every mechanical check (determinism, grapheme integrity, the
substitution spec) passes cleanly on them. Flagged to the user with
concrete examples; **verdict: "accept as is."** Recorded as a deliberate,
known tradeoff, not an oversight — the mechanism and the offensive-phrase
use case that motivated it both work as intended; a fraction of the
approved general-vocabulary bigrams simply abbreviate less naturally.

### 13.4 Mechanism and severity

The abbreviated form is a **fixed mechanical rule**, `initials()` — first
grapheme cluster of each word, joined as `"X. Y."` — defined once in
`src/noisers/abbreviate.py` and imported (not reimplemented) by the mining
script, so mining, review display, and generation can never disagree about
what an approved bigram produces. Unlike codemix, there is no
"propose-a-translation" step: once a bigram is approved, its abbreviated
form is a pure function of the two words.

A bigram *occurrence* is only eligible when its two words sit back-to-back
in the text with nothing but whitespace between them (matching exactly how
the lexicon was mined). Overlapping occurrences (e.g. three consecutive
words where both the first-two and last-two are independently approved)
are resolved by greedy left-to-right selection — the leftmost wins, and a
word already consumed by one substitution can never also be consumed by a
second in the same pass.

Coverage is inherently sparse and post-dependent — a post either contains
an eligible, back-to-back approved bigram or it doesn't — so severity uses
**codemix's forced-per-post model** rather than misspelling/
transliteration's probabilistic one: light abbreviates 1 occurrence if
present, heavy up to 2, both capped at whatever non-overlapping eligible
occurrences actually exist (never an error to have fewer). `n_substitutions`
is populated for every row — the second noiser after codemix to use that
schema field for real.

### 13.5 Verifier and final results

`check_abbreviate_substitution_spec` (`eval/invariants.py`) matches
`check_codemix_substitution_spec`'s rigor level deliberately, not more: it
reuses the noiser's own pure, non-random helper functions
(`_find_occurrences`, `_non_overlapping`) to recompute the eligible pool
from `original_text` and the frozen lexicon, then asserts
`n_substitutions == min(k, pool_size)` and that a zero-pool post is
byte-identical to its source. It does not attempt a byte-for-byte
reconstruction of exactly which occurrences the rng chose — that draw is
legitimately the rng's job, not independently re-derivable without
re-running it, the same reasoning codemix's own check applies. Four
regression cases cover a forced single occurrence, a forced two-occurrence
case, a no-eligible-bigram no-op, and the overlap-resolution guarantee on a
real lexicon triple.

| Metric | light | heavy |
|---|---|---|
| `TARGET_NOISE_RATE` (measured tripwire, not a target) | 0.0436 | 0.0518 |
| `noise_rate_error` | ~0.00001 | ~0.00002 |
| Posts touched | 32.79% (train) / 30.84% (test) | same |

The touch-rate ceiling is real and expected, not a bug: Channel B has no
fallback-to-unapproved mechanism the way codemix's plausible/eligible
fallback does — nothing fires beyond the 378 explicitly human-approved
bigrams, by deliberate safety-conscious design.

Full harness: **16/16 invariants, 21/21 regression (17 carried forward + 4
new abbreviate cases)**, `status: PASS`.

**Generated output**: `data/outputs/{train,test}/abbreviate_{light,heavy}.jsonl`
— 20,000 rows, same schema as Phases 2-4a. **Review artifacts**:
`data/lexicon/abbreviate_initialisms_candidates.md` (all 524 mined
candidates), `abbreviate_initialisms_final_wordlist.md` and `_removed.md`
(the filtered/audit views from the review rounds), and
`data/outputs/human_review_sample_abbreviate{,_changed_only}.{jsonl,md}`
(100-item samples, train-only, seed 1337).

With this, all four planned noise vectors (transliteration, codemix,
misspelling, abbreviation) are implemented, reviewed, and generated. The
compound pipeline (`src/pipeline.py`) and GATE B's full-scale, all-
conditions human sample remain open — see LOG.md for current status.

---

## 14. Reproducibility appendix

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
| `scripts/build_misspell_confusions.py` | Derives the IME-collision confusion sets and attestation vocabulary (§11.1) |
| `scripts/generate_misspell.py` | Generates the full misspell noised dataset (§11.4) |
| `scripts/build_abbreviate_initialisms.py` | Mines Channel B candidate bigrams and merges review approvals into the frozen lexicon (§13.2-13.3) |
| `scripts/generate_abbreviate.py` | Generates the full abbreviate noised dataset (§13.5) |
| `scripts/build_review_sample.py` | Builds a 100-item human-review sample for a given `--condition` (§8, §9.7, §11.3, §13.3) |
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
| Misspelling confusion sets (frozen) | `data/lexicon/misspell_confusions.jsonl` |
| Misspelling attestation vocabulary | `data/lexicon/misspell_attested_vocab.txt` |
| Misspelling confusion-set review | `data/lexicon/misspell_confusions_review.{csv,md}` |
| Generated misspell dataset | `data/outputs/{train,test}/misspell_{light,heavy}.jsonl` |
| Misspell human-review sample | `data/outputs/human_review_sample_misspell{,_changed_only}.{jsonl,md}` |
| Abbreviation initialism lexicon (frozen, 378 approved bigrams) | `data/lexicon/abbreviate_initialisms.jsonl` |
| Abbreviation candidate review / audit trail | `data/lexicon/abbreviate_initialisms_candidates.md`, `_final_wordlist.md`, `_removed.md` |
| Generated abbreviate dataset | `data/outputs/{train,test}/abbreviate_{light,heavy}.jsonl` |
| Abbreviate human-review sample | `data/outputs/human_review_sample_abbreviate{,_changed_only}.{jsonl,md}` |
| Full provenance record (URLs, hashes, counts) | `data/PROVENANCE.json` |
| Full evaluation report | `eval/report.json` / `eval/report.md` |
| Iteration-by-iteration project log | `LOG.md` |
