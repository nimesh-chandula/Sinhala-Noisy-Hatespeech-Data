# 4-bit QLoRA Fine-tuning

This document describes the current template implementation in `slm_qlora_4bit_training.py` and the synced notebook `slm_qlora_4bit_training.ipynb`.

The task is binary sequence classification for Sinhala offensive/hate speech:

- `0` / `NOT`: not offensive
- `1` / `OFF`: offensive

The script trains a PEFT LoRA adapter on one or more selected training conditions and evaluates each trained adapter on the configured test conditions.

## Source Files

- Script: `templates/slm_qlora_4bit_training.py`
- Notebook: `templates/slm_qlora_4bit_training.ipynb`
- Output root: `benchmark_results/qlora_4bit`

The notebook is synced from the Python script. Treat the `.py` file as the source of truth.

## Run Command

Run from the repository root:

```bash
cd ~/project/Sinhala-Noisy-Hatespeech-Data
source ~/.gpu-env/bin/activate
python -u templates/slm_qlora_4bit_training.py
```

For a background run:

```bash
nohup python -u templates/slm_qlora_4bit_training.py > qlora_run.log 2>&1 &
echo $! > qlora_run.pid
tail -f qlora_run.log
```

## Dependencies

Install once in the active Python environment:

```bash
python -m pip install -U "transformers>=4.45" "peft>=0.13" "accelerate>=1.0" "bitsandbytes>=0.46" "datasets>=3.0" pandas scikit-learn matplotlib seaborn huggingface_hub
```

A CUDA GPU with bitsandbytes support is required. The script stops immediately if CUDA is unavailable.

## Current Configuration

| Setting | Current value |
|---|---|
| `SEED` | `42` |
| `OUTPUT_ROOT` | `benchmark_results/qlora_4bit` |
| `TRAIN_DATASETS` | `['clean']` |
| `TEST_DATASETS` | `['clean', 'codemix_heavy', 'transliteration_heavy', 'compound_heavy', 'misspell_heavy']` |
| `TRAIN_SUBSET` | `None` |
| `ACTIVE_MODELS` | `['sinllama_gated']` |
| `EPOCHS` | `3.0` |
| `LEARNING_RATE` | `2e-4` |
| `TRAIN_BATCH_SIZE` | `8` |
| `EVAL_BATCH_SIZE` | `8` |
| `GRADIENT_ACCUMULATION_STEPS` | `4` |
| Effective batch size per GPU | `32` |
| `MAX_LENGTH` | `128` |
| `WEIGHT_DECAY` | `0.01` |
| `VALIDATION_FRACTION` | `0.10` |
| `LOGGING_STEPS` | `10` |

The model registry in the script is:

| Key | Hugging Face model |
|---|---|
| `qwen_4b` | `Qwen/Qwen3-4B` |
| `qwen_8b` | `Qwen/Qwen3-8B` |
| `llama_3b_gated` | `meta-llama/Llama-3.2-3B` |
| `llama_8b_gated` | `meta-llama/Llama-3.1-8B` |
| `sinllama_gated` | `polyglots/SinLlama_v01` |

Set `HF_TOKEN` before running gated models:

```bash
export HF_TOKEN=...
```

The script logs in with `HF_TOKEN` when it exists. If it is not set, ungated models may still load, but gated Llama-family models require approved Hugging Face access.

## Dataset Configuration

The script expects JSONL files under either the repository/data root or a matching Kaggle input directory. It auto-detects a root containing all selected train/test files, or you can set `DATA_ROOT` manually.

Supported dataset keys:

| Key | Train file | Test file |
|---|---|---|
| `clean` | `sold/train.jsonl` | `sold/test.jsonl` |
| `codemix_light` | `outputs/train/codemix_light.jsonl` | `outputs/test/codemix_light.jsonl` |
| `codemix_heavy` | `outputs/train/codemix_heavy.jsonl` | `outputs/test/codemix_heavy.jsonl` |
| `transliteration_light` | `outputs/train/transliteration_light.jsonl` | `outputs/test/transliteration_light.jsonl` |
| `transliteration_heavy` | `outputs/train/transliteration_heavy.jsonl` | `outputs/test/transliteration_heavy.jsonl` |
| `compound_light` | not configured for training | `outputs/test/compound_light.jsonl` |
| `compound_heavy` | `outputs/train/compound_heavy.jsonl` | `outputs/test/compound_heavy.jsonl` |
| `misspell_light` | not configured for training | `outputs/test/misspell_light.jsonl` |
| `misspell_heavy` | `outputs/train/misspell_heavy.jsonl` | `outputs/test/misspell_heavy.jsonl` |

Aliases are normalized before use:

| Alias | Normalized key |
|---|---|
| `codemix` | `codemix_heavy` |
| `transliteration` | `transliteration_heavy` |
| `compound` | `compound_heavy` |
| `misspell` | `misspell_heavy` |

Each JSONL file must contain a usable ID column, text column, and `label` column. Accepted ID column names are `post_id`, `source_id`, `id`, `sentence_id`, and `orig_id`. Accepted text column names are `text`, `noisy_text`, `transliterated`, `transliteration`, and `romanized`.

The loader converts labels such as `0`, `1`, `NOT`, `OFF`, `not-offensive`, `offensive`, `non-hate`, and `hate` into `0/1`. It rejects empty datasets, duplicate IDs, empty text, unknown labels, and aligned train/test variants whose labels disagree for the same IDs.

## Training Logic

The QLoRA script uses Hugging Face `Trainer` through a custom `WeightedTrainer`.

Pipeline:

1. Validate the selected datasets and models.
2. Load and canonicalize JSONL data.
3. Split the selected training condition into train and validation sets using a seeded, stratified 10 percent validation split.
4. Load the tokenizer with `trust_remote_code=True`, right padding, and EOS as pad token when no pad token exists.
5. Tokenize text with truncation to `MAX_LENGTH=128`.
6. Load `AutoModelForSequenceClassification` in 4-bit NF4 quantization.
7. Disable `use_cache`.
8. Prepare the quantized model for k-bit training with gradient checkpointing.
9. Attach LoRA adapters for sequence classification.
10. Train with class-weighted cross-entropy.
11. Select the best checkpoint by validation `macro_f1`.
12. Evaluate the final trainer on every configured test dataset.

## Quantization and LoRA Settings

| Setting | Value |
|---|---|
| 4-bit loading | `True` |
| Quantization type | `nf4` |
| Double quantization | `True` |
| Compute dtype | BF16 if supported, else FP16 |
| Device map | `auto` |
| Gradient checkpointing | enabled |
| Trainer optimizer | `paged_adamw_8bit` |
| Scheduler | cosine |
| Warmup ratio | `0.06` |
| Max grad norm | `0.3` |
| Group by length | `True` |
| Eval/save strategy | every epoch |
| Best model metric | `macro_f1` |

LoRA settings:

| Setting | Value |
|---|---|
| `task_type` | `SEQ_CLS` |
| `r` | `16` |
| `lora_alpha` | `32` |
| `lora_dropout` | `0.05` |
| `bias` | `none` |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` |
| Modules to save | detected from `score`, `classifier`, `classification_head` |

The script checks which target modules are present in the loaded model and only passes available module names to PEFT. If no target modules are found, it raises an error with available module leaves.

## Class Weights and Metrics

Class weights are calculated from the training split:

```text
weight[c] = number_of_training_examples / (2 * number_of_examples_in_class_c)
```

Metrics saved for validation/test include:

- accuracy
- balanced accuracy
- macro-F1
- `NOT` precision, recall, F1
- `OFF` precision, recall, F1

Macro-F1 is used for model selection because it gives equal importance to `NOT` and `OFF`.

## Output Files

For each model/train-condition pair, outputs are written to:

```text
benchmark_results/qlora_4bit/<model_name>/train_<train_condition>_seed42/
```

Important files:

| File or directory | Meaning |
|---|---|
| `checkpoints/` | Trainer checkpoints; only the best/final retained according to trainer settings |
| `adapter/` | PEFT adapter and tokenizer saved with `trainer.model.save_pretrained()` |
| `metrics.csv` | Test metrics for each configured test condition |
| `predictions.jsonl` | Example-level predictions for that run |
| `<test_condition>_classification_report.json` | Per-test-set sklearn report |
| `run_summary.json` | Run configuration, quantization settings, LoRA settings, and train metrics |

Global outputs under `benchmark_results/qlora_4bit/`:

| File | Meaning |
|---|---|
| `benchmark_summary_partial.csv` | Incremental summary during multi-run jobs |
| `benchmark_summary.csv` | Combined metrics for all completed runs |
| `all_predictions.jsonl` | Combined predictions for all completed runs |
| `macro_f1_matrix.csv` | Macro-F1 pivot table by model/train dataset/test dataset |
| `macro_f1_matrix.png` | Heatmap, if matplotlib/seaborn are installed |

## Important Compatibility Note

The current template loader directly calls `AutoModelForSequenceClassification.from_pretrained(model_id, ...)`. That works for models that can be loaded directly as sequence-classification models.

`polyglots/SinLlama_v01` is listed in `MODELS` and is currently selected in `ACTIVE_MODELS`, but SinLlama may require special PEFT adapter merge logic before sequence-classification training. If this generic QLoRA template fails for SinLlama, use the SinLlama-specific training script or merge its adapter-handling code into this template before cleaning the repository.

## What To Change For A New Run

Usually edit only these values:

```python
TRAIN_DATASETS = ["clean"]
TEST_DATASETS = ["clean", "codemix_heavy", "transliteration_heavy", "compound_heavy", "misspell_heavy"]
ACTIVE_MODELS = ["qwen_4b"]
TRAIN_SUBSET = None
```

Use `TRAIN_SUBSET = 200` or similar for a smoke test. Keep smoke-test outputs separate from full results.
