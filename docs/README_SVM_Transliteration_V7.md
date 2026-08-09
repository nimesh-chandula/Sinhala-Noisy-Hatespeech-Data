# SVM Transliteration V7 --- README

## 1. Project Overview

This notebook implements the **traditional machine-learning SVM
baseline** for the transliteration component of the Sinhala hate-speech
detection project.

The experiment evaluates whether an SVM trained on **character-level
TF-IDF representations** can classify transliterated Sinhala
social-media text as:

-   `0` --- not offensive
-   `1` --- offensive

The notebook focuses specifically on **Light** and **Heavy
transliteration noise**.

> **Scope:** This notebook is a transliteration-only experiment. Clean
> SOLD, other noise types, and multi-seed averaging are not included in
> this run.

------------------------------------------------------------------------

## 2. Experimental Objective

The main objectives are to:

1.  Build a traditional ML baseline using SVM.
2.  Use character-level TF-IDF features that are suitable for
    transliterated text.
3.  Tune the SVM kernel and regularization parameter using
    cross-validation.
4.  Train separate models on Light and Heavy transliteration data.
5.  Evaluate both models on both Light and Heavy test sets.
6.  Measure same-severity performance and cross-severity generalisation.
7.  Examine performance on the offensive class separately.
8.  Compare the SVM against simple majority/minority baselines.
9.  Perform error and robustness analysis.
10. Save trained models, predictions, results, and metadata for later
    comparison.

------------------------------------------------------------------------

## 3. Dataset

The notebook loads four JSONL datasets:

``` text
outputs/
├── train/
│   ├── transliteration_light.jsonl
│   └── transliteration_heavy.jsonl
└── test/
    ├── transliteration_light.jsonl
    └── transliteration_heavy.jsonl
```

Each record contains fields including:

-   `source_id` --- identifier of the original SOLD post
-   `noisy_text` --- transliterated text used as the model input
-   `label` --- classification target
-   `original_text`
-   `condition`
-   `severity`
-   `realised_noise_rate`
-   `generator_version`

The notebook uses:

``` text
TEXT_COL  = "noisy_text"
LABEL_COL = "label"
```

### Dataset sizes

  Split           Samples
  ------------- ---------
  Light train       7,500
  Light test        2,500
  Heavy train       7,500
  Heavy test        2,500

The training class distribution is:

  Class             Training Count   Proportion
  --------------- ---------------- ------------
  Not offensive              4,324       57.65%
  Offensive                  3,176       42.35%

The test class distribution is:

  Class             Test Count   Proportion
  --------------- ------------ ------------
  Not offensive          1,485       59.40%
  Offensive              1,015       40.60%

No missing values or duplicate texts were reported in the four splits.

------------------------------------------------------------------------

## 4. Data Validation and Leakage Checks

Before model training, the notebook performs several validation steps.

### 4.1 Dataset validation

Each split is checked for:

-   required columns
-   missing values
-   class distribution
-   class proportions
-   duplicate texts
-   unique labels

### 4.2 Light/Heavy test alignment

The Light and Heavy test sets are expected to represent the same
underlying posts at different transliteration severities.

The notebook checks the `source_id` values.

Actual run:

``` text
Light test source IDs : 2500
Heavy test source IDs : 2500
Common source IDs     : 2500
Only in Light         : 0
Only in Heavy         : 0
Aligned test posts    : 2500
Label mismatches      : 0
```

Therefore, the Light and Heavy test sets were verified to be aligned.

### 4.3 Train/test source-ID leakage check

The notebook checks all four train/test combinations:

``` text
Light train ∩ Light test
Light train ∩ Heavy test
Heavy train ∩ Light test
Heavy train ∩ Heavy test
```

Actual result:

``` text
LIGHT train ∩ LIGHT test : 0
LIGHT train ∩ HEAVY test : 0
HEAVY train ∩ LIGHT test : 0
HEAVY train ∩ HEAVY test : 0
```

Therefore, no `source_id` overlap was detected between training and
testing conditions.

------------------------------------------------------------------------

## 5. Feature Representation

The notebook uses **character-level TF-IDF**.

### Configuration

``` python
TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(1, 5),
    min_df=2,
    sublinear_tf=True
)
```

### Meaning

-   `analyzer="char_wb"` --- character-level features with word-boundary
    awareness.
-   `ngram_range=(1, 5)` --- 1-, 2-, 3-, 4-, and 5-character n-grams.
-   `min_df=2` --- character features appearing in fewer than two
    documents are ignored.
-   `sublinear_tf=True` --- applies sublinear term-frequency scaling.

Character n-grams are appropriate for transliterated text because
spelling variations can still share smaller character patterns.

The notebook does not add separate handcrafted features such as word
length, punctuation counts, sentiment features, or manually designed
transliteration features.

------------------------------------------------------------------------

## 6. Prevention of TF-IDF Data Leakage

The TF-IDF vectorizer is placed inside the same scikit-learn Pipeline as
the SVM:

``` text
Raw text
   ↓
Character TF-IDF
   ↓
SVM
```

The complete pipeline is passed to `GridSearchCV`.

This means that during each cross-validation fold, TF-IDF is fitted only
on that fold's training portion.

The test data is not used to fit the TF-IDF vocabulary or IDF
statistics.

This is an important methodological safeguard against feature leakage.

------------------------------------------------------------------------

## 7. Handling Class Imbalance

The dataset is moderately imbalanced toward the not-offensive class.

The SVM therefore uses:

``` python
class_weight="balanced"
```

This automatically gives greater training weight to the minority class.

The model-selection metric is:

``` text
Macro-F1
```

Macro-F1 gives equal importance to the two classes instead of allowing
the majority class to dominate the overall score.

The notebook also reports separate precision, recall, and F1 values for
both classes.

------------------------------------------------------------------------

## 8. SVM Configuration

The notebook uses scikit-learn `SVC`.

The hyperparameter grid is:

``` python
SVM_PARAM_GRID = {
    "svm__kernel": ["linear", "rbf"],
    "svm__C": [0.1, 1, 3, 10]
}
```

Therefore, the notebook automatically evaluates:

-   Linear + C=0.1
-   Linear + C=1
-   Linear + C=3
-   Linear + C=10
-   RBF + C=0.1
-   RBF + C=1
-   RBF + C=3
-   RBF + C=10

For each severity:

``` text
8 candidates × 5 CV folds = 40 fits
```

The best combination is selected automatically using cross-validated
Macro-F1.

No manual selection is made using the test-set results.

------------------------------------------------------------------------

## 9. Cross-Validation

The notebook uses:

-   5-fold cross-validation
-   Stratified folds
-   Macro-F1 as the scoring metric

The complete TF-IDF + SVM pipeline is evaluated within the CV procedure.

This means the model-selection process is based on the training data and
its CV folds, while the test sets remain reserved for final evaluation.

------------------------------------------------------------------------

## 10. Two SVM Models

Two independent models are trained.

### SVM-Light

Training data:

``` text
Light transliteration training set
```

### SVM-Heavy

Training data:

``` text
Heavy transliteration training set
```

The actual hyperparameter results were:

  Model       Best Kernel     Best C   CV Macro-F1
  ----------- ------------- -------- -------------
  SVM-Light   RBF                  1        0.7946
  SVM-Heavy   RBF                 10        0.7944

Both models selected the **RBF kernel** automatically.

------------------------------------------------------------------------

## 11. Four Evaluation Conditions

Each trained model is evaluated on both test severities.

### 1. Light → Light

Train on Light, test on Light.

This measures same-severity/in-domain performance for the Light model.

### 2. Light → Heavy

Train on Light, test on Heavy.

This measures whether the Light-trained model generalises to heavier
transliteration.

### 3. Heavy → Heavy

Train on Heavy, test on Heavy.

This measures same-severity/in-domain performance for the Heavy model.

### 4. Heavy → Light

Train on Heavy, test on Light.

This measures whether the Heavy-trained model generalises to lighter
transliteration.

------------------------------------------------------------------------

## 12. Final Results

### Core metrics

  Training   Testing     Accuracy     Macro-F1   Weighted-F1
  ---------- --------- ---------- ------------ -------------
  Light      Light         0.8116   **0.7983**        0.8081
  Light      Heavy         0.8072   **0.7923**        0.8027
  Heavy      Heavy         0.8080   **0.7944**        0.8043
  Heavy      Light         0.8100   **0.7972**        0.8068

Macro-F1 is the primary metric.

### Per-class results

  --------------------------------------------------------------------------------------------------------
  Training   Testing     Not-Offensive   Not-Offensive   Not-Offensive   Offensive   Offensive   Offensive
                             Precision          Recall              F1   Precision      Recall          F1
  ---------- --------- --------------- --------------- --------------- ----------- ----------- -----------
  Light      Light              0.8062          0.8990          0.8500      0.8223      0.6837      0.7466

  Light      Heavy              0.7976          0.9051          0.8479      0.8270      0.6640      0.7366

  Heavy      Heavy              0.8029          0.8970          0.8473      0.8181      0.6778      0.7414

  Heavy      Light              0.8072          0.8936          0.8482      0.8154      0.6877      0.7461
  --------------------------------------------------------------------------------------------------------

------------------------------------------------------------------------

## 13. Interpretation of the Results

### Best Macro-F1

The highest observed test Macro-F1 was:

``` text
Light-trained SVM → Light test
Macro-F1 = 0.7983
```

The Heavy-trained model on Light test was very close:

``` text
Macro-F1 = 0.7972
```

### Cross-severity generalisation

The two cross-severity results were:

``` text
Light → Heavy : Macro-F1 = 0.7923
Heavy → Light : Macro-F1 = 0.7972
```

The results are relatively close to the same-severity scores, indicating
that the trained models retained substantial performance when evaluated
at the other transliteration severity.

### Offensive-class recall

Offensive recall was:

``` text
Light → Light : 0.6837
Light → Heavy : 0.6640
Heavy → Heavy : 0.6778
Heavy → Light : 0.6877
```

The Heavy test condition produced lower offensive recall than the
corresponding Light test condition for both fixed models.

This is important because the model is considerably better at
recognizing the not-offensive class than the offensive class.

### Class-recall difference

The notebook calculates:

``` text
Offensive Recall − Not-Offensive Recall
```

Results:

``` text
Light → Light : -0.2152
Light → Heavy : -0.2410
Heavy → Heavy : -0.2191
Heavy → Light : -0.2059
```

The negative values show that offensive content is harder for the SVM to
detect than not-offensive content.

------------------------------------------------------------------------

## 14. Baseline Comparison

The notebook compares the SVM with simple majority and minority-class
baselines.

Baseline Macro-F1:

``` text
Majority baseline = 0.3726
Minority baseline = 0.2888
```

SVM Macro-F1:

``` text
Light → Light : 0.7983
Light → Heavy : 0.7923
Heavy → Heavy : 0.7944
Heavy → Light : 0.7972
```

The SVM beats both simple baselines in all four evaluation conditions.

------------------------------------------------------------------------

## 15. Confusion Matrices

The notebook generates a 2×2 confusion-matrix figure covering:

``` text
Light → Light
Light → Heavy
Heavy → Heavy
Heavy → Light
```

The matrices use:

``` text
Rows    = actual labels
Columns = predicted labels
```

They allow inspection of:

-   true negatives
-   false positives
-   false negatives
-   true positives

The notebook places particular emphasis on false negatives because they
correspond to offensive posts that the model failed to identify.

------------------------------------------------------------------------

## 16. Error Analysis

The notebook performs false-negative and false-positive analysis.

### False negatives

These are:

``` text
Actual = offensive
Predicted = not offensive
```

For each condition, the notebook examines examples closest to the SVM
decision boundary.

### False positives

These are:

``` text
Actual = not offensive
Predicted = offensive
```

Again, examples closest to the decision boundary are examined.

This helps identify difficult or ambiguous transliterated examples.

------------------------------------------------------------------------

## 17. Feature Analysis

The notebook contains a character n-gram coefficient analysis for Linear
SVM models.

However, in this actual run:

``` text
SVM-Light  → RBF
SVM-Heavy  → RBF
```

Therefore, coefficient-based linear feature analysis was automatically
skipped.

This is expected because an RBF SVM does not provide the same direct
linear coefficient interpretation as a linear SVM.

This does not affect the trained model or evaluation results.

------------------------------------------------------------------------

## 18. Degradation / Severity Analysis

The notebook compares Light-test and Heavy-test performance for the same
trained model.

Actual Macro-F1 values:

### SVM-Light

``` text
Light test = 0.7983
Heavy test = 0.7923
Difference = +0.0061 when calculated as Light − Heavy
```

### SVM-Heavy

``` text
Light test = 0.7972
Heavy test = 0.7944
Difference = +0.0028 when calculated as Light − Heavy
```

The corresponding offensive-recall differences are:

``` text
SVM-Light : +0.0197
SVM-Heavy : +0.0099
```

Importantly, the Macro-F1 difference is small, while offensive recall
shows a clearer decrease on Heavy test data.

> **Interpretation caution:** the notebook calls this section
> "degradation", but the measured Macro-F1 values do not show a large
> Heavy-test performance drop in this run. The more noticeable severity
> effect is on offensive recall. This should be described carefully in
> the final report rather than claiming a large overall degradation.

------------------------------------------------------------------------

## 19. Output Files

The notebook saves the following artifacts into:

``` text
/content/drive/MyDrive/Sinhala-Noisy-Hatespeech-Data/svm_artifacts/
```

### Trained models

``` text
svm_pipeline_light.joblib
svm_pipeline_heavy.joblib
```

Each saved pipeline contains the fitted TF-IDF transformer and SVM
model.

### Prediction files

``` text
svm_predictions_light_train__light_test.csv
svm_predictions_light_train__heavy_test.csv
svm_predictions_heavy_train__heavy_test.csv
svm_predictions_heavy_train__light_test.csv
```

Each prediction file contains 2,500 test predictions.

### Results

``` text
svm_transliteration_results.csv
```

This is the main machine-readable results table.

### Metadata

``` text
svm_metadata_light.json
svm_metadata_heavy.json
```

These store model and TF-IDF configuration information for
reproducibility.

### Figures

The notebook also generates visualizations for:

-   class distribution
-   confusion matrices
-   performance heatmaps
-   offensive vs not-offensive recall

------------------------------------------------------------------------

## 20. Reproducibility

The notebook uses:

``` python
RANDOM_STATE = 42
```

and:

``` text
5-fold Stratified Cross-Validation
```

The fitted models, results, predictions, and metadata are saved so that
later experiments can use the same artifacts.

------------------------------------------------------------------------

## 21. Important Methodological Notes

### What is included

-   Transliteration Light condition
-   Transliteration Heavy condition
-   Character TF-IDF
-   1--5 character n-grams
-   Linear and RBF SVM candidates
-   C tuning
-   5-fold Stratified CV
-   Macro-F1 model selection
-   Class-weight balancing
-   Same-severity evaluation
-   Cross-severity evaluation
-   Source-ID leakage checks
-   Error analysis
-   Baseline comparison

### What is not included

This notebook intentionally does not include:

-   Clean SOLD training/evaluation
-   Code-mixing
-   Misspelling
-   Abbreviation
-   Compound noise
-   Encoder models such as mBERT/XLM-R
-   SLM models
-   Multi-seed averaging

These are planned for other stages of the broader project.

------------------------------------------------------------------------

## 22. How to Run the Notebook

### Environment

The notebook is designed for **Google Colab**.

### Steps

1.  Open the notebook in Google Colab.
2.  Mount Google Drive.
3.  Ensure the four JSONL files exist at the expected paths.
4.  Run the notebook from top to bottom.
5.  Allow `GridSearchCV` to complete for both Light and Heavy models.
6.  Check the final verification report.
7.  Review the generated results and prediction files in
    `svm_artifacts`.

### Important

Because the notebook searches:

``` text
2 kernels × 4 C values × 5 folds
```

there are:

``` text
40 fits per severity
80 CV fits in total
```

for the two SVM models.

Therefore, training can take considerably longer than the earlier
linear-only version.

------------------------------------------------------------------------

## 23. Final Experimental Summary

The completed run produced:

``` text
SVM-Light
Best kernel = RBF
Best C      = 1
CV Macro-F1 = 0.7946

SVM-Heavy
Best kernel = RBF
Best C      = 10
CV Macro-F1 = 0.7944
```

Final test Macro-F1:

``` text
Light → Light = 0.7983
Light → Heavy = 0.7923
Heavy → Heavy = 0.7944
Heavy → Light = 0.7972
```

The SVM exceeded the majority-class baseline in all four conditions.

The strongest class-specific observation is that **offensive recall is
consistently lower than not-offensive recall**, particularly under the
Heavy test condition.

The experiment therefore provides a useful **traditional ML baseline for
transliterated Sinhala hate-speech detection** and a reference point for
later encoder/SLM and multi-noise experiments.
