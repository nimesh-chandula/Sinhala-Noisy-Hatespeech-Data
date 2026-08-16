# XGBoost Transliteration Baseline — Training, Testing and Results

**Source notebooks:** [XgBoost/NLP_14 (1).ipynb](../XgBoost/NLP_14%20(1).ipynb) and
[XgBoost/NLP_15.ipynb](../XgBoost/NLP_15.ipynb)

This document records the training setup, evaluation protocol, and measured
results of the **XGBoost traditional-ML baseline** for Sinhala hate-speech
detection on transliterated ("Singlish") noisy text.

Every number in this document is taken from the stored cell outputs of the two
notebooks. Nothing has been re-run or re-estimated.

---

## 1. Relationship between the two notebooks

| Notebook | Contents | Executed cells with stored output |
|---|---|---|
| `NLP_14 (1).ipynb` | Sections 1–11: setup, data loading, features, tuning, training, evaluation, degradation check | All core cells |
| `NLP_15.ipynb` | Sections 1–11 **identical to NLP_14**, plus Sections 12–19 "Additional Analysis" | Core cells + most analysis cells |

`NLP_15.ipynb` is a superset of `NLP_14 (1).ipynb`. The training/evaluation code
is byte-identical between the two, and both runs produced **exactly the same
metrics** (macro-F1 0.8128 light / 0.8041 heavy), which confirms the run is
deterministic under `RANDOM_STATE = 42`.

**Treat `NLP_15.ipynb` as the authoritative notebook.** `NLP_14 (1).ipynb` is
retained as the earlier, analysis-free version.

---

## 2. Experimental objective

The notebook implements the traditional-ML baseline of the project proposal
(Section 5.3.1) and aims to:

1. Train a gradient-boosted tree classifier (XGBoost) on noisy transliterated
   Sinhala social-media text.
2. Train and evaluate **separately** on Light and Heavy transliteration
   severity.
3. Use only the feature representation the proposal specifies — character
   n-gram TF-IDF plus word n-gram TF-IDF, no handcrafted features.
4. Handle class imbalance via `scale_pos_weight`.
5. Tune hyperparameters with **leakage-safe** cross-validation (TF-IDF refit
   inside each fold).
6. Report macro-F1, per-class precision/recall/F1, weighted-F1, accuracy, and a
   confusion matrix, against a majority-class baseline.
7. Provide supporting analysis: ROC/PR curves, bootstrap confidence intervals,
   feature importances, and qualitative error samples.

Labels are binary:

- `0` — not offensive
- `1` — offensive

---

## 3. Data

### 3.1 Files consumed

The notebook reads four JSONL files from Google Drive:

```text
transliterations/
├── train/
│   ├── transliteration_light.jsonl
│   └── transliteration_heavy.jsonl
└── test/
    ├── transliteration_light.jsonl
    └── transliteration_heavy.jsonl
```

These correspond to [data/outputs/train/](../data/outputs/train/) and
[data/outputs/test/](../data/outputs/test/) in this repository.

### 3.2 Fields used

```python
TEXT_COL  = "noisy_text"     # model input
LABEL_COL = "label"          # target
```

The model **only ever sees `noisy_text`** — the clean `original_text` field is
never used for training or inference. `source_id` is used later (Section 16 of
the notebook) to match Light and Heavy posts for paired statistical testing.

### 3.3 Split sizes and class balance

| Split | Rows | Not-offensive | Offensive | Offensive rate |
|---|---:|---:|---:|---:|
| Light train | 7,500 | 4,324 | 3,176 | 42.35% |
| Heavy train | 7,500 | 4,324 | 3,176 | 42.35% |
| Light test | 2,500 | 1,485 | 1,015 | 40.60% |
| Heavy test | 2,500 | 1,485 | 1,015 | 40.60% |

Light and Heavy are two noisings of the same underlying SOLD posts, so their
label distributions are identical by construction.

Data validation performed in the notebook is limited to a hard assertion that
`noisy_text` and `label` columns exist, plus a printed label distribution. Unlike
the SVM notebook, **this notebook does not run explicit `source_id` train/test
leakage checks** — see §11.

---

## 4. Feature representation

Two TF-IDF vectorizers are combined with a `FeatureUnion`:

```python
char_vec = TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(1, 5),
    min_df=2,
    max_features=30000,
    sublinear_tf=True,
)

word_vec = TfidfVectorizer(
    analyzer="word",
    ngram_range=(1, 2),
    min_df=2,
    max_features=15000,
    sublinear_tf=True,
    token_pattern=r"(?u)\b\w+\b",
)

features = FeatureUnion([("char_tfidf", char_vec), ("word_tfidf", word_vec)])
```

| Setting | Value | Rationale |
|---|---|---|
| Character analyzer | `char_wb`, 1–5 grams | Word-boundary-aware character n-grams survive spelling variation in transliterated text |
| Word analyzer | `word`, 1–2 grams | Captures whole romanized tokens and short phrases |
| `min_df=2` | Both | Drops hapax features |
| `max_features` | 30,000 char + 15,000 word | Caps the feature space at ≤45,000 dimensions for Colab memory |
| `sublinear_tf=True` | Both | Log-scaled term frequency |

No handcrafted features (length, punctuation, sentiment, lexicon hits) are added.

---

## 5. Model and pipeline

```python
clf = xgb.XGBClassifier(
    objective="binary:logistic",
    eval_metric="logloss",
    tree_method="hist",
    device=XGB_DEVICE,          # "cuda" if nvidia-smi succeeds, else "cpu"
    random_state=42,
    n_jobs=-1,
    scale_pos_weight=spw,
)

pipe = Pipeline([("features", features), ("clf", clf)], memory=cache_dir)
```

Both recorded runs report `XGBoost device: cuda` — the runs were GPU-accelerated,
though the code falls back to CPU cleanly.

### 5.1 Class imbalance handling

`scale_pos_weight` is computed from the training label counts only:

```text
scale_pos_weight = n_neg / n_pos = 4324 / 3176 = 1.361
```

This is identical for Light and Heavy, since both share the same label vector.
Because it is derived from labels rather than text, it is not a source of
*feature* leakage.

### 5.2 Leakage-safe cross-validation

The TF-IDF vectorizers sit **inside** the pipeline, and `RandomizedSearchCV`
receives **raw text**, not a pre-built matrix:

```text
raw noisy_text → FeatureUnion(char TF-IDF + word TF-IDF) → XGBClassifier
```

scikit-learn therefore clones and refits the whole pipeline — vectorizers
included — on each fold's training portion. The held-out fold's text never
contributes to vocabulary or IDF statistics for that fold. This is the key
methodological safeguard, and the notebook's own markdown calls it out as the
change that "removes the TF-IDF leakage".

A `Pipeline(memory=cache_dir)` disk cache means candidates that differ only in
XGBoost hyperparameters reuse the already-computed TF-IDF matrix for that fold
instead of recomputing it, which is what makes fold-wise refitting affordable on
Colab's free tier. The cache directory is deleted in Section 11.

---

## 6. Hyperparameter search

`RandomizedSearchCV` with 20 sampled candidates and 5 stratified folds:

```python
param_dist = {
    "clf__n_estimators":     randint(150, 600),
    "clf__max_depth":        randint(3, 10),
    "clf__learning_rate":    uniform(0.01, 0.29),
    "clf__subsample":        uniform(0.6, 0.4),
    "clf__colsample_bytree": uniform(0.5, 0.5),
    "clf__min_child_weight": randint(1, 8),
    "clf__gamma":            uniform(0, 0.5),
    "clf__reg_alpha":        uniform(0, 1.0),
    "clf__reg_lambda":       uniform(0.5, 2.0),
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
search = RandomizedSearchCV(pipe, param_dist, n_iter=20,
                            scoring="f1_macro", cv=cv,
                            random_state=42, n_jobs=-1)
```

| Quantity | Value |
|---|---|
| Candidates per severity | 20 |
| CV folds | 5 |
| Fits per severity | 100 |
| **Total CV fits (both severities)** | **200** |
| Selection metric | `f1_macro` |
| Final refit | `refit=True` — best pipeline refit on the full training set |

Model selection uses **only** cross-validated training-set macro-F1. The test
sets are never consulted during tuning.

### 6.1 Selected hyperparameters

Both severities selected the **same** configuration. This is expected rather
than surprising: `RandomizedSearchCV` is seeded with `random_state=42`, so the
same 20 candidates are drawn for both severities, and the same candidate won in
each case.

| Parameter | Selected value |
|---|---|
| `n_estimators` | 534 |
| `max_depth` | 7 |
| `learning_rate` | 0.0249 |
| `subsample` | 0.7958 |
| `colsample_bytree` | 0.8048 |
| `min_child_weight` | 1 |
| `gamma` | 0.2513 |
| `reg_alpha` | 0.2396 |
| `reg_lambda` | 0.7898 |
| `scale_pos_weight` | 1.361 |

| Model | CV macro-F1 (best) |
|---|---:|
| XGBoost-Light | 0.8057 |
| XGBoost-Heavy | 0.8030 |

---

## 7. Evaluation protocol

Each severity's tuned pipeline is evaluated on the **matching severity's test
set only**:

- Light-trained model → Light test set (2,500 posts)
- Heavy-trained model → Heavy test set (2,500 posts)

The notebook does **not** perform cross-severity evaluation (Light→Heavy or
Heavy→Light). That is a difference from the SVM notebook — see §11.

Metrics reported per severity: accuracy, macro-F1, weighted-F1, per-class
precision/recall/F1/support, confusion matrix, and a `DummyClassifier`
majority-class macro-F1 baseline.

---

## 8. Results

### 8.1 Headline metrics

| Severity | Accuracy | **Macro-F1** | Weighted-F1 | CV macro-F1 | Majority baseline macro-F1 |
|---|---:|---:|---:|---:|---:|
| Light | 0.8232 | **0.8128** | 0.8211 | 0.8057 | 0.3726 |
| Heavy | 0.8152 | **0.8041** | 0.8129 | 0.8030 | 0.3726 |

Test macro-F1 slightly exceeds CV macro-F1 in both cases (+0.0071 light,
+0.0011 heavy), i.e. no sign of overfitting to the CV folds.

The model beats the majority-class baseline by a wide margin in both conditions
(≈ +0.44 macro-F1).

### 8.2 Per-class results

**Light severity**

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| not-offensive (0) | 0.8249 | 0.8916 | 0.8570 | 1,485 |
| offensive (1) | 0.8201 | 0.7232 | 0.7686 | 1,015 |
| macro avg | 0.8225 | 0.8074 | 0.8128 | 2,500 |
| weighted avg | 0.8230 | 0.8232 | 0.8211 | 2,500 |

**Heavy severity**

| Class | Precision | Recall | F1 | Support |
|---|---:|---:|---:|---:|
| not-offensive (0) | 0.8179 | 0.8862 | 0.8507 | 1,485 |
| offensive (1) | 0.8103 | 0.7113 | 0.7576 | 1,015 |
| macro avg | 0.8141 | 0.7988 | 0.8041 | 2,500 |
| weighted avg | 0.8148 | 0.8152 | 0.8129 | 2,500 |

### 8.3 Confusion matrices

Rows = true label, columns = predicted label.

**Light**

|  | pred: not-offensive | pred: offensive |
|---|---:|---:|
| **true: not-offensive** | 1,324 (TN) | 161 (FP) |
| **true: offensive** | 281 (FN) | 734 (TP) |

**Heavy**

|  | pred: not-offensive | pred: offensive |
|---|---:|---:|
| **true: not-offensive** | 1,316 (TN) | 169 (FP) |
| **true: offensive** | 293 (FN) | 722 (TP) |

Moving from Light to Heavy costs 12 additional false negatives and 8 additional
false positives.

### 8.4 Threshold-independent metrics

Computed from `predict_proba` for the offensive class:

| Severity | ROC AUC | Average Precision |
|---|---:|---:|
| Light | 0.8861 | 0.8684 |
| Heavy | 0.8814 | 0.8620 |

The AUC gap between severities (0.0047) is smaller than the macro-F1 gap
(0.0086), which suggests part of the Light→Heavy difference is about where the
0.5 decision threshold falls rather than about ranking quality collapsing.

### 8.5 Bootstrap 95% confidence intervals

2,000 bootstrap resamples of the test predictions (`RANDOM_STATE = 42`):

| Severity | Macro-F1 | 95% CI | Bootstrap std |
|---|---:|---|---:|
| Light | 0.8128 | [0.7973, 0.8276] | 0.0076 |
| Heavy | 0.8041 | [0.7880, 0.8198] | 0.0081 |

This resamples already-computed predictions rather than retraining across seeds,
so it quantifies test-set sampling variability only — not training variance.

---

## 9. Severity / degradation analysis

```text
Macro-F1 (light noise): 0.8128
Macro-F1 (heavy noise): 0.8041
Performance drop (light → heavy): 0.0086
```

Derived differences (Light − Heavy):

| Metric | Light | Heavy | Difference |
|---|---:|---:|---:|
| Accuracy | 0.8232 | 0.8152 | +0.0080 |
| Macro-F1 | 0.8128 | 0.8041 | +0.0086 |
| Offensive recall | 0.7232 | 0.7113 | +0.0118 |
| Offensive F1 | 0.7686 | 0.7576 | +0.0110 |
| ROC AUC | 0.8861 | 0.8814 | +0.0047 |

**Interpretation caveat.** The notebook's own print statement labels this
"heavier noise hurts more", and directionally every metric does move that way.
But the magnitude is small and the two bootstrap confidence intervals overlap
substantially ([0.7973, 0.8276] vs [0.7880, 0.8198]). The measured degradation
should therefore be described as **a small, consistently-signed effect**, not as
a demonstrated large drop. The notebook includes a McNemar's exact test
specifically to settle this question — but see §10.2, it was not executed.

### 9.1 Class-recall asymmetry

| Severity | Offensive recall − not-offensive recall |
|---|---:|
| Light | −0.1684 |
| Heavy | −0.1749 |

The dominant, robust finding is not the severity effect but the **class
asymmetry**: the model is substantially better at recognising not-offensive
content than offensive content, in both conditions. False negatives (offensive
posts missed) outnumber false positives roughly 1.7:1.

---

## 10. Supporting analysis (NLP_15 only)

Sections 12–19 of `NLP_15.ipynb` are read-only analysis on top of the already
fitted pipelines. Section 12 re-predicts from the stored pipelines and confirms
the macro-F1 values reproduce exactly (0.8128 / 0.8041), so nothing below
changes any headline number.

### 10.1 Executed analyses

| Section | Analysis | Output |
|---|---|---|
| 13 | Confusion-matrix heatmaps | `analysis/confusion_matrices.png` |
| 14 | ROC + PR curves, AUC/AP | `analysis/roc_pr_curves.png`, values in §8.4 |
| 15 | Bootstrap 95% CIs | `analysis/bootstrap_confidence_intervals.csv`, values in §8.5 |
| 18 | Feature importances (top 25 per severity) | `analysis/feature_importance_{light,heavy}.{png,csv}` |
| 19 | Sampled false positives / false negatives | `analysis/false_{negatives,positives}_sample_{light,heavy}.csv` |

### 10.2 Cells present but **not executed**

Two analysis cells contain code but have **no stored output** in
`NLP_15.ipynb`, meaning they were not run in the saved session:

| Section | Analysis | Status |
|---|---|---|
| 16 | McNemar's exact test (Light vs Heavy, matched by `source_id`) | **No results recorded** |
| 17 | OOV character n-gram rate (tokenization-fragmentation proxy) | **No results recorded** |

This matters for the write-up: the notebook's statistical-significance test of
the severity effect, and its fragmentation analysis, are **implemented but
unreported**. Any claim that the Light/Heavy difference is statistically
significant is currently unsupported by this notebook. Both cells should be run
before these analyses are cited.

### 10.3 Feature importance

Top-importance features are overwhelmingly **character n-grams**, and they
correspond to romanized Sinhala profanity and slur fragments rather than to
syntax or topic words.

| Rank | Light severity | Importance | Heavy severity | Importance |
|---:|---|---:|---|---:|
| 1 | `char: akkil` | 0.00629 | `char: puka` | 0.00799 |
| 2 | `char: " hu"` | 0.00616 | `char: akkil` | 0.00672 |
| 3 | `char: puk` | 0.00539 | `char: " hu"` | 0.00614 |
| 4 | `word: kalakanni` | 0.00483 | `char: " ponn"` | 0.00613 |
| 5 | `char: kkil` | 0.00473 | `char: kkil` | 0.00538 |

Observations:

- 23 of the top 25 Light features and 24 of the top 25 Heavy features are
  character n-grams; word n-grams barely appear. This validates the
  character-level representation choice for transliterated text.
- The two severities' top-feature lists overlap heavily but not identically —
  under Heavy noise the model leans on slightly shorter/more fragmented
  substrings (e.g. `wajat`, `ajath` appear in Heavy but not Light), consistent
  with heavier noise breaking longer stable spellings.
- Individual importances are low (max ≈ 0.008), i.e. the decision is spread
  across many weak features rather than driven by a handful of keywords.

### 10.4 Qualitative error analysis

| Severity | False negatives | False positives |
|---|---:|---:|
| Light | 281 | 161 |
| Heavy | 293 | 169 |

The most confident errors, ordered by predicted probability, show two recurring
patterns:

- **False negatives** (offensive posts scored ≈0.09–0.12 offensive) tend to be
  short, contextually-offensive posts with no explicit slur token — e.g.
  `@USER ado eki jana wikrithi una ekakda?`. The model's signal is lexical, so
  offensiveness carried by context rather than vocabulary is missed.
- **False positives** (not-offensive posts scored ≈0.90–0.99 offensive) contain
  strong slur-like character n-grams used non-abusively or quoted — e.g. posts
  containing `kalakanni`, `pako`, `hujja`. The same lexical shortcut that drives
  recall drives these errors.

Notably, several individual posts fail under **both** severities (e.g. test rows
1507, 827, 655, 527 as false negatives; rows 306, 2220, 1106, 2082, 45 as false
positives), which indicates a core of intrinsically hard posts independent of
noise level.

---

## 11. Comparison with the SVM baseline

Against [README_SVM_Transliteration_V7.md](README_SVM_Transliteration_V7.md),
using the same-severity conditions (the only ones XGBoost ran):

| Condition | SVM macro-F1 | XGBoost macro-F1 | Δ |
|---|---:|---:|---:|
| Light → Light | 0.7983 | **0.8128** | +0.0145 |
| Heavy → Heavy | 0.7944 | **0.8041** | +0.0097 |

| Condition | SVM offensive recall | XGBoost offensive recall | Δ |
|---|---:|---:|---:|
| Light → Light | 0.6837 | **0.7232** | +0.0395 |
| Heavy → Heavy | 0.6778 | **0.7113** | +0.0335 |

XGBoost outperforms the RBF SVM on both severities, and the gain is
concentrated in **offensive-class recall** — the class that matters most for
this task. Precision on the offensive class is essentially unchanged (SVM 0.8223
/ 0.8181 vs XGBoost 0.8201 / 0.8103), so the improvement is a genuine recall
gain rather than a precision/recall trade.

Both models reproduce the same qualitative finding: offensive recall is well
below not-offensive recall. XGBoost narrows the gap (−0.168 / −0.175) relative
to the SVM (−0.215 / −0.219) but does not close it.

### 11.1 Scope differences between the two notebooks

| Aspect | SVM V7 | XGBoost NLP_15 |
|---|---|---|
| Same-severity evaluation | Yes | Yes |
| Cross-severity evaluation (L→H, H→L) | Yes | **No** |
| Explicit `source_id` leakage checks | Yes | **No** |
| Light/Heavy test alignment check | Yes | Implicit only (via the unexecuted McNemar cell) |
| ROC/PR, AUC/AP | No | Yes |
| Bootstrap CIs | No | Yes |
| Feature importance actually reported | No (RBF selected, so skipped) | Yes |
| Interpretable per-feature signal | No | Yes |

The comparison in §11 is like-for-like on the conditions both ran. Extending
XGBoost to cross-severity evaluation would make the two directly comparable
across all four conditions.

---

## 12. Reproducibility

| Item | Value |
|---|---|
| Random seed | `RANDOM_STATE = 42` (numpy, StratifiedKFold, RandomizedSearchCV, XGBClassifier, bootstrap RNG) |
| CV | 5-fold stratified, shuffled |
| Environment | Google Colab, GPU (`device="cuda"`, `tree_method="hist"`) |
| Packages | `xgboost`, `scikit-learn`, `scipy`, `joblib` — installed with `--upgrade`, **versions not pinned** |

The two notebook runs (`NLP_14` and `NLP_15`) produced byte-identical metrics,
which is direct empirical evidence that the run is deterministic under this seed.

**Reproducibility gap:** package versions are not pinned, and no
`pip freeze` output is stored. Exact reproduction on a future Colab image is not
guaranteed. Pinning `xgboost` and `scikit-learn` versions in
[requirements.txt](../requirements.txt) would close this.

---

## 13. Output artifacts

Written to `<BASE_DIR>/results/xgboost/`:

**Core (Sections 1–11)**

```text
xgboost_pipeline_light.joblib      # fitted FeatureUnion + XGBClassifier
xgboost_pipeline_heavy.joblib
test_predictions_light.csv         # 2,500 rows + predicted_label + predicted_proba_offensive
test_predictions_heavy.csv
xgboost_results_summary.csv        # one row per severity, all metrics + best_params
```

**Analysis (Sections 12–19, `NLP_15` only)** — written to
`results/xgboost/analysis/`:

```text
confusion_matrices.png
roc_pr_curves.png
bootstrap_confidence_intervals.csv
feature_importance_light.png / .csv
feature_importance_heavy.png / .csv
false_negatives_sample_light.csv   /  false_positives_sample_light.csv
false_negatives_sample_heavy.csv   /  false_positives_sample_heavy.csv
```

Not produced, because the corresponding cells were not executed:
`oov_fragmentation_summary.csv`, `oov_rate_distribution.png`.

Each saved `.joblib` contains the fitted vectorizers **and** the model, so
inference on raw text is a single `pipeline.predict(texts)` call.

---

## 14. Known limitations and methodological notes

1. **No cross-severity evaluation.** Each model is only tested on its own
   severity, so the notebook cannot say whether a Light-trained model
   generalises to Heavy noise. The SVM notebook answers this; XGBoost does not.
2. **McNemar's test and the OOV/fragmentation analysis were not run.** The code
   exists (Sections 16–17) but has no stored output, so the severity effect has
   no significance test attached in this run.
3. **No `source_id` leakage check.** The notebook assumes the upstream splits
   are disjoint. The SVM notebook verified this independently (0 overlap across
   all four combinations), which provides indirect assurance for the same files,
   but this notebook does not verify it itself.
4. **Majority baseline is fit on the test set.** In `evaluate()`,
   `DummyClassifier` is fit on `(X_test, y_test)`. `DummyClassifier` ignores `X`
   and `strategy="most_frequent"` only reads the label distribution, so the
   resulting 0.3726 is correct as a *test-set* majority baseline — but it is not
   a held-out baseline in the strict sense. Worth stating precisely if quoted in
   a paper.
5. **Identical hyperparameters across severities** are a consequence of the
   shared search seed, not evidence that the two severities prefer the same
   configuration. Do not present it as a finding.
6. **Bootstrap CIs are not multi-seed CIs.** They capture test-set sampling
   variability, not training variability. The proposal's original multi-seed
   protocol would additionally capture the latter.
7. **Single run, single seed.** No seed averaging was performed for the training
   itself.
8. **Transliteration only.** Clean SOLD, code-mixing, misspelling, abbreviation,
   and compound noise conditions are out of scope here, as are encoder models
   (mBERT/XLM-R) and SLMs.

---

## 15. Suggested next steps

1. Execute Sections 16 and 17 of `NLP_15.ipynb` to obtain the McNemar p-value
   and the OOV fragmentation numbers — these are already written and cheap to
   run, and they close the two largest reporting gaps.
2. Add cross-severity evaluation (Light→Heavy, Heavy→Light) to make the XGBoost
   results directly comparable with the SVM's four-condition table.
3. Add the explicit `source_id` leakage check for parity with the SVM notebook.
4. Pin package versions.
5. Consider decision-threshold tuning on the offensive class: AUC (0.886/0.881)
   is meaningfully higher than the F1 at the default 0.5 threshold implies,
   suggesting recall could be improved at modest precision cost.

---

## 16. Summary

```text
XGBoost-Light   CV macro-F1 = 0.8057   Test macro-F1 = 0.8128   AUC = 0.8861
XGBoost-Heavy   CV macro-F1 = 0.8030   Test macro-F1 = 0.8041   AUC = 0.8814

Majority baseline macro-F1 = 0.3726 (both severities)
Light → Heavy macro-F1 difference = 0.0086 (bootstrap CIs overlap)
```

XGBoost on character + word TF-IDF is a strong traditional-ML baseline for
transliterated Sinhala hate-speech detection, beating the RBF SVM by
+0.015 / +0.010 macro-F1 and, more importantly, by +0.04 / +0.03 offensive-class
recall. The heavier transliteration severity degrades performance slightly and
consistently in sign, but the effect is small and — in this run — statistically
untested. The persistent, well-supported finding is that offensive content
remains harder to detect than non-offensive content at both severities, with the
model relying on lexical slur fragments that both drive its recall and cause its
most confident false positives.
