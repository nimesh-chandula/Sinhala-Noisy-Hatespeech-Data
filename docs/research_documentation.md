# Research Documentation — Sinhala Noise Dataset Builder

**Purpose of this document:** a complete, factually-precise reference of
data sources, methodology, tools tested, metrics, and results produced
during this project, intended as raw material for a research paper — not
polished paper prose. Every number below is sourced from a specific file
in the repository (cited inline) so it can be independently re-verified.

**Status as of writing:** Phase 0 (verifier) and Phase 1 (romanizer
selection) are complete. Phase 2 (transliteration noiser) is complete but
paused at a mandatory manual-review checkpoint before the next *noise*
phase (code-mixing) begins — see §8. In parallel with that pause, the
Phase-2 transliteration output has been used to train and evaluate the
first downstream hate-speech classifiers (SVM and XGBoost baselines) —
see §9–§12. That parallel track is deliberate but carries a caveat
recorded in §12.4: the classifiers were trained on data whose human
review is still pending.

**Scope note on the classifier sections (§9–§12):** both notebooks train
and evaluate at *both* transliteration severities, but **this document
records only the `heavy` severity condition**. Heavy is the harder,
more discriminating condition and the one this project's benchmarking
argument rests on. The light-severity numbers, and the light/heavy
degradation analysis, are documented separately in
[README_SVM_Transliteration_V7.md](README_SVM_Transliteration_V7.md) and
[README_XGBoost_Transliteration.md](README_XGBoost_Transliteration.md).

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
| 2 | Build the transliteration noiser; generate real output | Complete, paused at manual review |
| 3 (not started) | Code-mixing noise vector | — |
| 4 (not started) | Misspelling / abbreviation noise vectors | — |
| 5 (not started) | Full dataset generation | — |
| 6 | Downstream classifier baselines on the transliteration output (SVM, XGBoost) | Complete for the transliteration condition (§9–§12) |

**Chronological reading order.** The document is ordered by when the work
happened: data acquisition and gold-set construction (§2), verifier design
(§3), romanizer bake-off (§4–§5), noiser construction and dataset
generation (§6–§8), then downstream model training and results on the
generated dataset (§9–§12), then reproducibility (§13). Everything from §9
onward consumes the artifact produced in §7 and adds nothing to it.

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
| `realism_jsd` — transliteration_light | 0.1030 | ≤ 0.0766 (30% reduction) | ❌ (5.82% actual) |
| `realism_jsd` — transliteration_heavy | 0.1039 | ≤ 0.0766 (30% reduction) | ❌ (5.07% actual) |
| `noise_rate_error` — light | 0.00029 | < 0.05 | ✅ |
| `noise_rate_error` — heavy | 0.00013 | < 0.05 | ✅ |
| Invariants (13 checks) | all pass | all pass | ✅ |
| Regression suite (8 cases) | all pass | all pass | ✅ |

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
  the project's process design, work stops here for human validation of a
  100-item transliteration sample (`data/outputs/human_review_sample.md`,
  50 light + 50 heavy severity, drawn from the train split only, seed
  1337) regardless of whether the numeric realism target was hit. As of
  this writing, that review is pending.
- **A note on methodology transparency:** several fixes and design
  decisions in this project were discovered only by deliberately measuring
  and diagnosing metric behavior (e.g. the v→w and ත/ට romanizer fixes,
  the uniform-vs-closest-variant selection finding, the per-post seed
  bug) rather than being apparent from inspection alone. This is
  presented as a feature of the verifier-first methodology, not
  incidental — every fix in this document has a measured before/after
  number attached to it.

---

## 9. Downstream classifier baselines — shared experimental setup

Phases 0–2 produced a dataset; §9–§12 record what happened when
hate-speech classifiers were actually trained on it. Two traditional-ML
baselines were run, in this order:

| # | Model | Notebook | Purpose |
|---|---|---|---|
| 1 | Linear/RBF SVM on character TF-IDF | `SVM/SVM_Transliteration_V7.ipynb` | First baseline; establishes that the noised data is learnable at all |
| 2 | XGBoost on character + word TF-IDF | `XgBoost/NLP_15.ipynb` | Stronger baseline; tests whether a non-linear ensemble improves on the SVM |

`XgBoost/NLP_14 (1).ipynb` is an earlier version of the XGBoost notebook
containing the same training and evaluation code; it produced
byte-identical metrics and is superseded by `NLP_15.ipynb`, which adds
read-only analysis sections on top. Both are retained.

**As stated in the scope note above, only the `heavy` transliteration
condition is recorded below.**

### 9.1 Data consumed

Both notebooks read the Phase-2 output described in §7:

```text
data/outputs/train/transliteration_heavy.jsonl   # 7,500 rows
data/outputs/test/transliteration_heavy.jsonl    # 2,500 rows
```

(In the notebooks these are read from a Google Drive copy at
`transliterations/{train,test}/transliteration_heavy.jsonl`; the content
is the same generated artifact.)

Of the schema's nine fields (§7), the classifiers use exactly two:

| Field | Role |
|---|---|
| `noisy_text` | model input |
| `label` | target (0 = not offensive, 1 = offensive) |

**The clean `original_text` field is never used for training or
inference in either notebook.** This is the point of the whole exercise —
the classifier only ever sees the noised text. `source_id` is used only
for leakage checking and for matching posts across severities.

### 9.2 Class distribution

Inherited unchanged from SOLD (§2.1), since the noiser rewrites text
without touching labels:

| Split | Rows | Not-offensive | Offensive | Offensive rate |
|---|---:|---:|---:|---:|
| Heavy train | 7,500 | 4,324 | 3,176 | 42.35% |
| Heavy test | 2,500 | 1,485 | 1,015 | 40.60% |

Both notebooks confirmed these counts at load time, and both match the
provenance-verified SOLD figures in §2.1 exactly — an end-to-end check
that the noiser preserved label integrity across 10,000 rows.

### 9.3 Leakage controls

Two distinct leakage risks were relevant, and they were handled
differently by the two notebooks:

**(a) Split leakage (`source_id` appearing in both train and test).**
Guaranteed upstream by SOLD's own split isolation (§2.1) and by the
noiser preserving `source_id`. The **SVM notebook verified this
independently**, checking all four train/test severity combinations and
finding zero overlap in every case:

```text
LIGHT train ∩ LIGHT test : 0
LIGHT train ∩ HEAVY test : 0
HEAVY train ∩ LIGHT test : 0
HEAVY train ∩ HEAVY test : 0
```

The **XGBoost notebook does not perform this check** and relies on the
upstream guarantee. Since both notebooks consume the same files, the
SVM's verification covers the XGBoost run in practice — but it is not
verified within that notebook.

**(b) Feature leakage (TF-IDF fitted on data it will later be scored
on).** Both notebooks handle this the same, correct way: the TF-IDF
vectorizer(s) sit *inside* a scikit-learn `Pipeline` whose last step is
the classifier, and the whole pipeline — not a pre-computed feature
matrix — is what gets handed to the hyperparameter search. scikit-learn
therefore clones and refits the vectorizers on each CV fold's training
portion only, so a held-out fold's text never contributes to the
vocabulary or IDF statistics used to score it. The final refit on the
full training set, performed once after hyperparameters are chosen, is
standard and is not leakage.

The XGBoost notebook additionally attaches a `Pipeline(memory=...)` disk
cache so that candidates differing only in tree hyperparameters reuse
the fold's already-computed TF-IDF matrix instead of recomputing it —
which is what makes per-fold refitting affordable on Colab's free tier.

### 9.4 Shared evaluation protocol

| Aspect | Setting |
|---|---|
| Model-selection metric | Macro-F1 (equal weight to both classes, so the 58/42 imbalance cannot be gamed by predicting the majority) |
| Cross-validation | 5-fold stratified, shuffled |
| Test set | Held out entirely from tuning; used once, at the end |
| Reported metrics | Accuracy, macro-F1, weighted-F1, per-class precision/recall/F1, confusion matrix |
| Baseline comparison | `DummyClassifier(strategy="most_frequent")` majority-class macro-F1 |
| Seed | `RANDOM_STATE = 42` in both notebooks |

**Seed note for §13:** the classifier notebooks use seed 42, *not* the
project-wide seed 1337 used for all data generation. The two seeds govern
disjoint stages (1337 fixes which data exists; 42 fixes how models are
fit to it), so this is not a conflict — but it must be stated rather than
assumed.

---

## 10. Baseline 1 — SVM (heavy transliteration)

Source: `SVM/SVM_Transliteration_V7.ipynb`; full write-up in
[README_SVM_Transliteration_V7.md](README_SVM_Transliteration_V7.md).

### 10.1 Features

Character-level TF-IDF only:

```python
TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 5),
                min_df=2, sublinear_tf=True)
```

Character n-grams rather than words, because transliterated Sinhala has
no stable orthography — the same word is spelled several ways (this is
precisely the property the Phase-2 noiser injects, §6.1), so word-level
features fragment while shared character substrings survive. No
handcrafted features (length, punctuation counts, sentiment, lexicon
hits) were added.

### 10.2 Model and tuning

`sklearn.svm.SVC` with `class_weight="balanced"` to compensate for the
42.35% offensive rate, tuned by exhaustive grid search:

```python
SVM_PARAM_GRID = {"svm__kernel": ["linear", "rbf"],
                  "svm__C": [0.1, 1, 3, 10]}
```

8 candidates × 5 folds = **40 fits** for the heavy model.

| Selected | Value |
|---|---|
| Kernel | RBF (selected automatically over linear) |
| `C` | 10 |
| CV macro-F1 | 0.7944 |

The RBF kernel winning has a downstream consequence: the notebook's
character-n-gram coefficient analysis only applies to linear SVMs, so it
was automatically skipped. **The SVM baseline therefore yields no
interpretable per-feature signal** — a gap the XGBoost run later filled
(§11.5).

### 10.3 Results — heavy train → heavy test

| Metric | Value |
|---|---:|
| Accuracy | 0.8080 |
| **Macro-F1** | **0.7944** |
| Weighted-F1 | 0.8043 |

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| not-offensive (0) | 0.8029 | 0.8970 | 0.8473 | 1,485 |
| offensive (1) | 0.8181 | 0.6778 | 0.7414 | 1,015 |

| Baseline | Macro-F1 |
|---|---:|
| Majority-class | 0.3726 |
| Minority-class | 0.2888 |
| **SVM** | **0.7944** |

Confusion matrix (reconstructed from the reported per-class
precision/recall and supports — the SVM notebook plots the matrices
rather than printing them; the reconstruction reproduces both reported
precisions to four decimal places, so it is exact):

|  | pred: not-offensive | pred: offensive |
|---:|---:|---:|
| **true: not-offensive** | 1,332 (TN) | 153 (FP) |
| **true: offensive** | 327 (FN) | 688 (TP) |

### 10.4 Principal finding

Offensive recall (0.6778) is **0.2192 below** not-offensive recall
(0.8970). The model is markedly better at recognising non-offensive
content than offensive content: nearly a third of offensive posts are
missed. Since false negatives are the costly error type for a hate-speech
system, this asymmetry — not the headline macro-F1 — is the SVM
baseline's most important result.

---

## 11. Baseline 2 — XGBoost (heavy transliteration)

Source: `XgBoost/NLP_15.ipynb`; full write-up in
[README_XGBoost_Transliteration.md](README_XGBoost_Transliteration.md).

### 11.1 Features

Character TF-IDF **plus** word TF-IDF, combined with a `FeatureUnion`:

```python
char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 5),
                           min_df=2, max_features=30000, sublinear_tf=True)
word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2),
                           min_df=2, max_features=15000, sublinear_tf=True,
                           token_pattern=r"(?u)\b\w+\b")
```

Two differences from the SVM: word 1–2 grams are added, and both
vectorizers are capped by `max_features` (≤45,000 dimensions total) for
Colab memory. §11.5 shows the word features turned out to contribute
almost nothing.

### 11.2 Model and tuning

`xgb.XGBClassifier(objective="binary:logistic", eval_metric="logloss",
tree_method="hist", device="cuda")`, with class imbalance handled by
`scale_pos_weight = n_neg / n_pos = 4324 / 3176 = 1.361` — computed from
labels only, so not a source of feature leakage.

Tuned by `RandomizedSearchCV` over nine hyperparameters
(`n_estimators`, `max_depth`, `learning_rate`, `subsample`,
`colsample_bytree`, `min_child_weight`, `gamma`, `reg_alpha`,
`reg_lambda`), 20 sampled candidates × 5 folds = **100 fits** for the
heavy model.

| Selected | Value |
|---|---:|
| `n_estimators` | 534 |
| `max_depth` | 7 |
| `learning_rate` | 0.0249 |
| `subsample` | 0.7958 |
| `colsample_bytree` | 0.8048 |
| `min_child_weight` | 1 |
| `gamma` | 0.2513 |
| `reg_alpha` | 0.2396 |
| `reg_lambda` | 0.7898 |
| CV macro-F1 | 0.8030 |

### 11.3 Results — heavy train → heavy test

| Metric | Value |
|---|---:|
| Accuracy | 0.8152 |
| **Macro-F1** | **0.8041** |
| Weighted-F1 | 0.8129 |
| CV macro-F1 (for comparison) | 0.8030 |

Test macro-F1 slightly *exceeds* CV macro-F1 (+0.0011), i.e. no evidence
of overfitting to the CV folds.

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| not-offensive (0) | 0.8179 | 0.8862 | 0.8507 | 1,485 |
| offensive (1) | 0.8103 | 0.7113 | 0.7576 | 1,015 |

Confusion matrix (printed directly by the notebook):

|  | pred: not-offensive | pred: offensive |
|---:|---:|---:|
| **true: not-offensive** | 1,316 (TN) | 169 (FP) |
| **true: offensive** | 293 (FN) | 722 (TP) |

Majority-class baseline macro-F1: 0.3726.

### 11.4 Threshold-independent metrics and confidence interval

| Metric | Value |
|---|---:|
| ROC AUC (offensive class) | 0.8814 |
| Average Precision | 0.8620 |
| Macro-F1 95% CI (2,000 bootstrap resamples) | [0.7880, 0.8198] |
| Bootstrap std | 0.0081 |

The confidence interval resamples already-computed test predictions, so
it captures **test-set sampling variability only**, not training
variance. It is a lighter-weight substitute for a multi-seed protocol,
not equivalent to one.

The gap between AUC (0.8814) and the macro-F1 achieved at the default 0.5
threshold suggests the ranking is better than the hard predictions
imply — i.e. threshold tuning is an unexploited lever for improving
offensive recall.

### 11.5 Feature importance — what the model actually keys on

The XGBoost run supplies the interpretability the RBF SVM could not
(§10.2). Top features for the heavy condition:

| Rank | Feature | Importance |
|---:|---|---:|
| 1 | `char: puka` | 0.00799 |
| 2 | `char: akkil` | 0.00672 |
| 3 | `char: " hu"` | 0.00614 |
| 4 | `char: " ponn"` | 0.00613 |
| 5 | `char: kkil` | 0.00538 |

Three observations, each of which bears on the dataset design rather
than just the model:

1. **24 of the top 25 features are character n-grams**; word n-grams are
   almost absent despite being 15,000 of the ~45,000 available
   dimensions. This is direct empirical support for the character-level
   representation choice, and it independently corroborates §6.1's
   premise that spelling variance destroys word-level stability in
   transliterated text.
2. **The top features are romanized profanity/slur fragments**, not
   syntax or topic words — the model is running a lexical
   pattern-matcher, which explains both its recall ceiling and its error
   profile (§12.3).
3. **Individual importances are low** (max ≈ 0.008), so the decision is
   spread thinly across many weak features rather than driven by a
   handful of keywords.

### 11.6 Error profile

| Error type | Count (of 2,500) |
|---|---:|
| False negatives (offensive missed) | 293 |
| False positives (non-offensive flagged) | 169 |

The most confident errors fall into two clean patterns:

- **False negatives** (scored ≈0.09–0.12 offensive) are short posts that
  are offensive *in context* but contain no explicit slur token — e.g.
  `@USER ado eki jan wikrithi una ekakda?`. A lexical model has nothing
  to fire on.
- **False positives** (scored ≈0.90–0.99 offensive) contain strong
  slur-like character n-grams used non-abusively or quoted — e.g. posts
  containing `kalakanni`, `pako`, `hujja`. The same shortcut that
  produces recall produces these.

### 11.7 Analyses implemented but not executed

Two analysis cells in `NLP_15.ipynb` contain complete code but have **no
stored output**, meaning they were not run in the saved session:

| Notebook section | Analysis | Status |
|---|---|---|
| 16 | McNemar's exact test across severities, matched by `source_id` | **No results recorded** |
| 17 | OOV character-n-gram rate (tokenization-fragmentation proxy) | **No results recorded** |

This is recorded here because §17 in particular is directly relevant to
this project's methodology: it would have measured how badly heavy noise
fragments text into n-grams the model has never seen, which is the
model-side counterpart to the realism/JSD measurements in §3.2. **No
fragmentation number exists yet.** Both cells are written and cheap to
run.

---

## 12. Baseline comparison and findings

### 12.1 Head-to-head (heavy transliteration, identical train/test files)

| Metric | SVM (RBF) | XGBoost | Δ |
|---|---:|---:|---:|
| Accuracy | 0.8080 | **0.8152** | +0.0072 |
| **Macro-F1** | 0.7944 | **0.8041** | **+0.0097** |
| Weighted-F1 | 0.8043 | **0.8129** | +0.0086 |
| CV macro-F1 | 0.7944 | **0.8030** | +0.0086 |
| Not-offensive precision | 0.8029 | **0.8179** | +0.0150 |
| Not-offensive recall | **0.8970** | 0.8862 | −0.0108 |
| Not-offensive F1 | 0.8473 | **0.8507** | +0.0034 |
| Offensive precision | **0.8181** | 0.8103 | −0.0078 |
| **Offensive recall** | 0.6778 | **0.7113** | **+0.0335** |
| Offensive F1 | 0.7414 | **0.7576** | +0.0162 |
| Majority baseline | 0.3726 | 0.3726 | — |

In error counts:

| | SVM | XGBoost | Δ |
|---|---:|---:|---:|
| Offensive posts caught (TP) | 688 | **722** | **+34** |
| Offensive posts missed (FN) | 327 | **293** | **−34** |
| Non-offensive posts wrongly flagged (FP) | **153** | 169 | +16 |

**XGBoost is the better baseline**, and the gain is concentrated exactly
where it matters: it recovers 34 additional offensive posts (+3.35pp
recall) at a cost of 16 additional false positives. Offensive precision
falls only 0.0078, so this is a genuine recall gain, not a
precision-for-recall trade dressed up as an improvement.

### 12.2 Both models clear the trivial baselines decisively

| Model | Macro-F1 | vs. majority baseline (0.3726) |
|---|---:|---:|
| SVM | 0.7944 | +0.4218 |
| XGBoost | 0.8041 | +0.4315 |

The heavily-noised transliteration dataset is comfortably learnable —
heavy spelling variance does not render the signal inaccessible to
traditional ML. This is the primary sanity result for the Phase-2
artifact.

*Baseline caveat:* in the XGBoost notebook the `DummyClassifier` is fit
on `(X_test, y_test)`. `DummyClassifier` ignores `X` and
`strategy="most_frequent"` reads only the label distribution, so 0.3726
is correct as a *test-set* majority baseline — but it is not held out in
the strict sense, and should be described that way if quoted.

### 12.3 The consistent, cross-model finding

| Model | Offensive recall | Not-offensive recall | Gap |
|---|---:|---:|---:|
| SVM | 0.6778 | 0.8970 | **−0.2192** |
| XGBoost | 0.7113 | 0.8862 | **−0.1749** |

Both models are substantially worse at detecting offensive content than
non-offensive content, under two different feature sets, two different
model families, and two different imbalance-correction mechanisms
(`class_weight="balanced"` vs `scale_pos_weight`). XGBoost narrows the
gap by 0.0443 but does not close it, and both still miss roughly
28–32% of offensive posts.

§11.5 and §11.6 together explain why: the signal these models extract is
**lexical** — romanized slur fragments — so offensiveness carried by
context, sarcasm, or implication is invisible to them, while innocuous
posts containing slur-shaped substrings are over-flagged. This is a
ceiling imposed by the representation, not by the tuning, which is
consistent with a stronger tuner (100 fits vs 40) buying only +0.0097
macro-F1.

### 12.4 Limitations of the classifier baselines

1. **Trained on data whose human review is still pending.** §8 records
   that Phase 2 stops unconditionally at a 100-item manual-review
   checkpoint, and that review has not been completed. The classifier
   results are therefore valid as *baselines on the generated artifact*,
   but they inherit any quality issue the review may yet surface. They
   do not substitute for that review.
2. **No fragmentation measurement.** The OOV-rate analysis that would
   connect model performance back to this project's realism/JSD
   framework was implemented but not run (§11.7).
3. **No statistical test across conditions.** The McNemar test was
   likewise not run (§11.7), so no significance claim is available for
   any cross-condition difference.
4. **Single seed, no seed averaging.** Both notebooks run once at
   `RANDOM_STATE = 42`. The XGBoost bootstrap CI (§11.4) captures test
   sampling variability only, not training variance.
5. **XGBoost package versions unpinned.** The notebook installs with
   `pip install -q --upgrade xgboost scikit-learn scipy joblib` and
   stores no `pip freeze`, so exact reproduction on a future Colab image
   is not guaranteed — a weaker reproducibility position than the rest of
   this project maintains (§13).
6. **Transliteration only.** Clean SOLD, code-mixing, misspelling,
   abbreviation, and compound-noise conditions were not evaluated, since
   Phases 3–5 have not started. Encoder models (mBERT/XLM-R) and SLMs are
   likewise out of scope for these two baselines.
7. **The SVM's features are uninterpretable.** RBF selection meant no
   coefficient analysis was possible (§10.2), so the feature-level
   findings in §11.5 come from XGBoost alone and are not corroborated by
   a second model.

### 12.5 Immediate next steps

1. Complete the §8 manual review — it gates everything downstream.
2. Run notebook sections 16–17 (`NLP_15.ipynb`) to obtain the McNemar
   p-value and the OOV fragmentation rate; both are written and cheap.
3. Pin classifier package versions.
4. Explore decision-threshold tuning for the offensive class, which
   §11.4's AUC/F1 gap indicates is an unexploited lever.
5. Treat XGBoost macro-F1 **0.8041** and offensive recall **0.7113** as
   the reference numbers the planned encoder/SLM models must beat on the
   heavy transliteration condition.

---

## 13. Reproducibility appendix

**Seeds.** Two seeds govern two disjoint stages, and both must be quoted
to reproduce an end-to-end result:

| Seed | Stage | Scope |
|---|---|---|
| `1337` | Data generation (§2–§7) | All sampling, shuffling, and noise-generation randomness, directly or via a stable per-item hash (`zlib.crc32`, not Python's `hash()` — see §6.5) |
| `42` | Classifier training (§9–§12) | numpy, `StratifiedKFold`, `GridSearchCV`/`RandomizedSearchCV`, `SVC`/`XGBClassifier`, bootstrap RNG |

Seed 1337 fixes *which data exists*; seed 42 fixes *how models are fit to
it*. Determinism of the classifier stage under seed 42 is not merely
asserted — the two XGBoost notebook runs (`NLP_14 (1)` and `NLP_15`)
produced byte-identical metrics, which is direct empirical evidence.

**Environment note:** the classifier notebooks were run on Google Colab
with GPU (`device="cuda"`, `tree_method="hist"` for XGBoost) and install
their dependencies **unpinned** (§12.4, item 5). The data-generation
stage has no such gap.

**Key scripts** (all runnable from the repository root):

| Script | Purpose |
|---|---|
| `scripts/fetch_data.py` | Fetches SOLD and Swa-Bhasha data, builds gold/reference sets (§2) |
| `scripts/verify_uom_endpoint.py` | One-time 20-item live calibration of `uom_rules.py` (§4.3, stage 1) |
| `scripts/fetch_uom_bakeoff.py` | One-time 2,400-item bulk fetch for the `uom_live` backend (§4.3, stage 2) |
| `scripts/build_word_variants.py` | Builds the transliteration noiser's word-variant lexicon (§6.2) |
| `scripts/generate_transliteration.py` | Generates the full noised dataset (§7); also has a `--demo` mode for ad-hoc text |
| `scripts/build_review_sample.py` | Builds the 100-item human-review sample (§8) |
| `eval/harness.py` | Runs the full evaluation suite; produces `eval/report.json` / `.md` |

**Classifier notebooks** (Google Colab; consume the §7 output, produce
the §10–§11 results):

| Notebook | Purpose |
|---|---|
| `SVM/SVM_Transliteration_V7.ipynb` | SVM baseline — training, tuning, evaluation, leakage checks (§10) |
| `SVM/SVM_Transliteration_V6.ipynb` | Earlier SVM version, superseded by V7 |
| `XgBoost/NLP_15.ipynb` | XGBoost baseline + analysis sections — authoritative (§11) |
| `XgBoost/NLP_14 (1).ipynb` | Earlier XGBoost version; identical metrics, no analysis sections |

Per-notebook write-ups, including the light-severity results excluded
from this document by scope: `docs/README_SVM_Transliteration_V7.md` and
`docs/README_XGBoost_Transliteration.md`.

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
| Generated noised dataset | `data/outputs/{train,test}/transliteration_{light,heavy}.jsonl` |
| Human-review sample | `data/outputs/human_review_sample.{jsonl,md}` |
| Full provenance record (URLs, hashes, counts) | `data/PROVENANCE.json` |
| Full evaluation report | `eval/report.json` / `eval/report.md` |
| Iteration-by-iteration project log | `LOG.md` |

**Classifier artifacts** (written to Google Drive by the notebooks, not
committed to this repository):

| Artifact | Path (relative to the notebook's results dir) |
|---|---|
| Fitted SVM pipelines (TF-IDF + SVC) | `svm_artifacts/svm_pipeline_heavy.joblib` |
| SVM test predictions | `svm_artifacts/svm_predictions_heavy_train__heavy_test.csv` |
| SVM results table / metadata | `svm_artifacts/svm_transliteration_results.csv`, `svm_metadata_heavy.json` |
| Fitted XGBoost pipeline (TF-IDF + XGBClassifier) | `results/xgboost/xgboost_pipeline_heavy.joblib` |
| XGBoost test predictions (with offensive probability) | `results/xgboost/test_predictions_heavy.csv` |
| XGBoost results table | `results/xgboost/xgboost_results_summary.csv` |
| XGBoost analysis outputs (ROC/PR, CIs, feature importance, error samples) | `results/xgboost/analysis/` |

Each saved `.joblib` bundles the fitted vectorizer(s) *and* the model, so
inference on raw noisy text is a single `pipeline.predict(texts)` call.
