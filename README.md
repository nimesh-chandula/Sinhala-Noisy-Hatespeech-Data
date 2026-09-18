# Sinhala Noisy Hate-Speech Benchmark

This repository introduces a benchmark for evaluating Sinhala offensive and
hate-speech classifiers under realistic social-media noise. Starting from the
[SOLD](https://huggingface.co/datasets/sinhala-nlp/SOLD) dataset, we create
aligned clean and noisy train/test sets, then evaluate classical machine
learning models and small language models (SLMs) across the resulting
conditions.

The benchmark is designed to answer a practical question: how well does a
model trained on clean Sinhala continue to detect offensive content when the
same text is written as Singlish, mixed with English, or contains spelling
noise?

## Benchmark tasks

Each post retains its original binary label: `0` for not offensive and `1` for
offensive. Models can be trained and tested on the following conditions:

| Condition | Description |
| --- | --- |
| `clean` | Original SOLD Sinhala text. |
| `transliteration_light` / `transliteration_heavy` | Sinhala text written in Latin-script Singlish. |
| `codemix_light` / `codemix_heavy` | Sinhala text with English substitutions. |
| `misspell_light` / `misspell_heavy` | Text with realistic spelling noise. |
| `compound_light` / `compound_heavy` | Multiple noise types applied together. |
| `all_noise_light` / `all_noise_heavy` | Combined benchmark noise settings. |

This supports clean-to-noisy robustness testing, matched train/test evaluation,
and cross-condition evaluation (for example, train on clean text and test on
heavy code-mixed text). Results, tables, and reproduced figures are kept under
`results/finalresults/reproduced_outputs/`.

## Project layout

```text
data/
  sold/                         Original SOLD train/test JSONL files
  outputs/train/ and outputs/test/
                                Generated benchmark conditions
  gold/, reference/, lexicon/   Evaluation references and noise resources

SLMs/
  encoders/                     Encoder-model notebooks: XLM-R, SinBERT,
                                LaBSE, and HelaBERT
  decoders/                     Decoder-model QLoRA and classification-head
                                training scripts and notebooks
  sinllama/                     SinLLaMA-specific training, evaluation, and
                                saved model/result files

MNB/                            Multinomial Naive Bayes baseline notebook
SVM/                            Support Vector Machine experiment notebooks
XgBoost/                        XGBoost experiment notebooks
results/finalresults/           Final benchmark outputs and reproduced plots/tables

src/                            Noise-generation components and utilities
scripts/                        Dataset preparation and generation scripts
eval/                           Dataset quality checks and evaluation harness
docs/                           Method, fine-tuning, and experiment notes
```

## Models evaluated

The benchmark includes three model groups:

- Classical baselines: Multinomial Naive Bayes, SVM, and XGBoost.
- Encoder models: XLM-R (base and large), SinBERT, LaBSE, and HelaBERT.
- Decoder models: QLoRA/classification-head experiments for Llama, Qwen, and
  SinLLaMA. SinLLaMA has its own implementation in `SLMs/sinllama/`.

## How to use

1. Clone the repository and create a Python environment (Python 3.11+).

   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # Windows
   pip install -r requirements.txt
   ```

2. The benchmark JSONL files are in `data/sold/` (clean) and
   `data/outputs/train/` / `data/outputs/test/` (noisy conditions). Each row
   contains text, an identifier, and a binary `label`.

3. Run a model family from its notebook folder:

   - Classical baselines: `MNB/`, `SVM/`, or `XgBoost/`
   - Encoder experiments: `SLMs/encoders/`
   - Decoder experiments: `SLMs/decoders/`
   - SinLLaMA experiments: `SLMs/sinllama/`

   Select the desired training and test conditions in the notebook/script
   configuration, then run it in Jupyter or with Python. Decoder and SinLLaMA
   training requires a CUDA-capable GPU and the Hugging Face/PEFT dependencies
   described in `docs/`.

4. To verify the generated data or regenerate the noise conditions, run:

   ```bash
   python eval/harness.py
   python scripts/generate_transliteration.py
   python scripts/generate_codemix.py
   ```

   See `docs/research_documentation.md` for the generation methodology and
   quality checks.

## Data and license

SOLD is sourced from `sinhala-nlp/SOLD` on Hugging Face. The repository also
uses Swa-Bhasha resources for romanization evaluation and reference text.
Source provenance is recorded in `data/PROVENANCE.json`.

The repository code is licensed under the MIT License. Third-party datasets
and derived resources remain subject to their original terms.
