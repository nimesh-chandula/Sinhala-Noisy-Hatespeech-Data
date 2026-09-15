# 4-bit Classification-Head Training

This document describes the current template implementation in `slm_classification_head_4bit_training.py` and the synced notebook `slm_classification_head_training.ipynb`.

The task is binary sequence classification for Sinhala offensive/hate speech:

- `0` / `NOT`: not offensive
- `1` / `OFF`: offensive

This method freezes the quantized base model and trains only the sequence-classification head. It does not attach LoRA adapters.

## Source Files

- Script: `templates/slm_classification_head_4bit_training.py`
- Notebook: `templates/slm_classification_head_training.ipynb`
- Output root: `benchmark_results/classification_head_4bit`

The notebook is synced from the Python script. Treat the `.py` file as the source of truth.

## Run Command

Run from the repository root:

```bash
cd ~/project/Sinhala-Noisy-Hatespeech-Data
source ~/.gpu-env/bin/activate
python3 -u templates/slm_classification_head_4bit_training.py
```

For a background run:

```bash
nohup python3 -u templates/slm_classification_head_4bit_training.py > classification_head_run.log 2>&1 &
echo $! > classification_head_run.pid
tail -f classification_head_run.log
```

## Dependencies

Install once in the active Python environment:

```bash
python -m pip install -U "transformers>=4.45" "accelerate>=1.0" "bitsandbytes>=0.46" "datasets>=3.0" pandas scikit-learn matplotlib seaborn huggingface_hub tqdm
```

A CUDA GPU with bitsandbytes support is required. The script stops immediately if CUDA is unavailable.

## Current Configuration

| Setting | Current value |
|---|---|
| `SEED` | `42` |
| `OUTPUT_ROOT` | `benchmark_results/classification_head_4bit` |
| `TRAIN_DATASETS` | `['compound_heavy']` |
| `TEST_DATASETS` | `['clean', 'codemix_heavy', 'transliteration_heavy', 'compound_heavy', 'misspell_heavy']` |
| `TRAIN_SUBSET` | `None` |
| `ACTIVE_MODELS` | `['llama_3b_gated']` |
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
| `EVAL_ACCUMULATION_STEPS` | `8` |
| `WARMUP_RATIO` | `0.06` |
| `MAX_GRAD_NORM` | `0.3` |
| `OPTIMIZER` | `paged_adamw_8bit` |

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

The script uses `HF_TOKEN` when available, otherwise it tries the local Hugging Face token cache through `get_token()`. No token should be hardcoded in the repository.

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

Each JSONL file must contain a usable ID column, text column, and `label` column. Accepted ID column names are `post_id`, `source_id`, `id`, `sentence_id`, and `orig_id`. Accepted text column names are `text`, `noisy_text`, `transliterated`, `transliteration`, and `romanized`.

The loader converts labels such as `0`, `1`, `NOT`, `OFF`, `not-offensive`, `offensive`, `non-hate`, and `hate` into `0/1`. It rejects empty datasets, duplicate IDs, empty text, unknown labels, and aligned train/test variants whose labels disagree for the same IDs.

Unlike the QLoRA script, this classification-head script does not currently define dataset aliases such as `codemix -> codemix_heavy`. Use the exact dataset keys shown above.

## Training Logic

The classification-head script uses a manual PyTorch training loop, not Hugging Face `Trainer`.

Pipeline:

1. Validate the selected datasets and models.
2. Load and canonicalize JSONL data.
3. Split the selected training condition into train and validation sets using a seeded, stratified 10 percent validation split.
4. Load the tokenizer with `trust_remote_code=True`, right padding, and EOS as pad token when no pad token exists.
5. Tokenize text with truncation to `MAX_LENGTH=128`.
6. Load `AutoModelForSequenceClassification` in 4-bit NF4 quantization.
7. Freeze every model parameter.
8. Unfreeze only parameters whose names contain `score`, `classifier`, or `classification_head`.
9. Train those head parameters with weighted cross-entropy.
10. Evaluate on the validation split after each epoch.
11. Keep the best trainable-head state by validation `macro_f1`.
12. Restore that best head state and evaluate on every configured test dataset.

The script raises an error if it cannot find a classification-head parameter to train.

## Quantization and Optimizer Settings

| Setting | Value |
|---|---|
| 4-bit loading | `True` |
| Quantization type | `nf4` |
| Double quantization | `True` |
| Compute dtype | BF16 if supported, else FP16 |
| Device map | `auto` |
| Attention implementation | `sdpa` |
| `use_cache` | `False` |
| Gradient checkpointing | enabled when supported by the model |
| Optimizer | bitsandbytes `PagedAdamW8bit` |
| Scheduler | cosine with warmup |
| Warmup ratio | `0.06` |
| Max grad norm | `0.3` |
| Mixed precision | `torch.autocast` on CUDA; gradient scaler enabled for FP16 |

Only the classification head is trained. The run summary records `lora: null` and `fine_tuning_method: classification_head_only_4bit`.

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

Macro-F1 is used to select the best head state because it gives equal importance to `NOT` and `OFF`.

## Output Files

For each model/train-condition pair, outputs are written to:

```text
benchmark_results/classification_head_4bit/<model_name>/train_<train_condition>_seed42/
```

Important files:

| File or directory | Meaning |
|---|---|
| `classification_head_state.pt` | Best trainable head weights selected by validation macro-F1 |
| `model/` | Tokenizer and model config, not a full saved quantized model |
| `metrics.csv` | Test metrics for each configured test condition |
| `predictions.jsonl` | Example-level predictions for that run |
| `<test_condition>_classification_report.json` | Per-test-set sklearn report |
| `run_summary.json` | Run configuration, quantization settings, trainable head names, and train metrics |

Global outputs under `benchmark_results/classification_head_4bit/`:

| File | Meaning |
|---|---|
| `benchmark_summary_partial.csv` | Incremental summary during multi-run jobs |
| `benchmark_summary.csv` | Combined metrics for all completed runs |
| `all_predictions.jsonl` | Combined predictions for all completed runs |
| `macro_f1_matrix.csv` | Macro-F1 pivot table by model/train dataset/test dataset |
| `macro_f1_matrix.png` | Heatmap, if matplotlib/seaborn are installed |

## Important Compatibility Note

The current template loader directly calls `AutoModelForSequenceClassification.from_pretrained(model_id, ...)`. That works for models that can be loaded directly as sequence-classification models.

`polyglots/SinLlama_v01` is present in the model registry, but SinLlama may require special PEFT adapter merge logic before sequence-classification training. If this generic classification-head template fails for SinLlama, use the SinLlama-specific training script or merge its adapter-handling code into this template before cleaning the repository.

## What To Change For A New Run

Usually edit only these values:

```python
TRAIN_DATASETS = ["compound_heavy"]
TEST_DATASETS = ["clean", "codemix_heavy", "transliteration_heavy", "compound_heavy", "misspell_heavy"]
ACTIVE_MODELS = ["llama_3b_gated"]
TRAIN_SUBSET = None
```

Use `TRAIN_SUBSET = 200` or similar for a smoke test. Keep smoke-test outputs separate from full results.
