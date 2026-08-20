# LoRA/QLoRA fine-tuning process

This document explains how the Sinhala hate-speech classifiers in this repository were fine-tuned, why the main parameters exist, and which experimental decisions were made. It is based on the notebooks in `llama8b/`, `sinllama/`, `qwen4b/`, and `qwen7b/` and, where available, the saved Qwen 4B run metadata.

## 1. Task and experimental question

The task is binary sequence classification:

- `NOT` (`0`): not offensive
- `OFF` (`1`): offensive

The experiments also test robustness to different written forms of Sinhala. A model is trained on one condition and then evaluated on several conditions:

- **clean**: original Sinhala script
- **transliteration light/heavy**: increasing amounts of romanized Sinhala
- **code-mix light/heavy**: increasing Sinhala/English mixing (Qwen experiments)

Keeping separate test conditions distinguishes in-domain performance from transfer to another noise type. For example, training on heavy transliteration and testing on clean Sinhala asks whether robustness learned from romanized text transfers back to the original script.

## 2. End-to-end training pipeline

Each notebook follows approximately the same pipeline.

1. **Choose a base model and training condition.** One adapter is trained for each selected condition.
2. **Load and validate JSONL data.** The code finds ID, text, and label columns; converts labels to `0/1`; rejects empty text, duplicate IDs, and unknown labels; and checks that noisy variants contain the same IDs and labels as clean data.
3. **Create a validation set.** Ten percent of the selected training set is removed using a seeded, stratified split, preserving approximately the same `NOT/OFF` distribution.
4. **Tokenize the text.** Input is truncated to 128 tokens. Padding is added dynamically per batch instead of padding every example to 128 tokens.
5. **Load the base model in 4-bit precision.** Frozen base weights use NF4 quantization with double quantization. Computation uses BF16 when supported and FP16 otherwise.
6. **Attach trainable LoRA adapters and a classification head.** LoRA is applied to attention and feed-forward projection layers. Most base-model parameters remain frozen.
7. **Train with class-weighted cross-entropy.** Minority-class errors receive a larger weight, reducing the tendency to predict only the majority class.
8. **Validate and checkpoint after every epoch.** The checkpoint with the highest validation macro-F1 is restored at the end.
9. **Evaluate the same adapter on every test condition.** Accuracy, 
balanced accuracy, macro-F1, and per-class precision/recall/F1 are saved with individual predictions.
10. **Save the adapter, tokenizer, and reports.** This is much smaller than saving a separate full model for every condition. The base model is still required when loading an adapter.

## 3. Model-specific configurations

| Experiment | Hugging Face model | Selected training data in notebook | Test data | Epochs | Device batch | Accumulation | Effective batch* |
|---|---|---|---|---:|---:|---:|---:|
| Llama 8B | `meta-llama/Meta-Llama-3-8B` | heavy transliteration | clean, light, heavy transliteration | 3 | 2 | 16 | 32 |
| SinLlama | `polyglots/SinLlama_v01` | heavy transliteration | clean, light, heavy transliteration | 1 | 2 | 16 | 32 |
| Qwen 4B | `Qwen/Qwen3-4B` | heavy transliteration | clean, light/heavy transliteration, light/heavy code-mix | 5 | 2 | 16 | 32 |
| Qwen 7B | `Qwen/Qwen2.5-7B-Instruct` | clean | clean, light/heavy transliteration, light/heavy code-mix | 3 | 1 | 32 | 32 |

\*Effective batch per optimizer update is `device batch × gradient accumulation × number of GPUs`. The table assumes one GPU.

The lists in the notebooks are configuration choices, not hard limitations. For a complete robustness matrix, change the training list to include all desired conditions. Each condition creates an independent adapter and is tested on every configured test set.

### SinLlama-specific loading

SinLlama is not loaded exactly like the other models. `polyglots/SinLlama_v01` may be a causal-language-model PEFT adapter over Llama 3 with saved token embeddings and language-model head. The notebook therefore:

1. loads the Llama base as a 4-bit causal LM;
2. resizes embeddings to match the SinLlama tokenizer;
3. attaches and merges the pretrained SinLlama adapter;
4. transfers the merged backbone into `LlamaForSequenceClassification`;
5. creates a new two-class `score` head; and
6. attaches a new classification LoRA adapter.

This preserves SinLlama's Sinhala language adaptation while changing the objective from next-token prediction to hate-speech classification. A tokenizer-fertility sanity check helps detect a missing extended Sinhala vocabulary: unusually many tokens per Sinhala word suggest that the intended tokenizer was not loaded.

## 4. Parameters and their purposes

### Data and reproducibility

| Parameter | Value | Purpose and reason for the choice |
|---|---:|---|
| `seed` | 42 | Controls NumPy/PyTorch randomness, validation splitting, shuffling, and adapter initialization. A fixed value makes runs comparable, although it does not guarantee bit-for-bit GPU determinism. |
| validation fraction | 0.10 | Reserves data for model selection without removing too much training data. The official test set is not used to select a checkpoint. |
| `train_subset` | disabled | Can limit rows for a smoke test. It is disabled for full experiments so all training examples are used. |
| `max_length` | 128 | Caps memory and runtime for short social-media posts. Longer examples are truncated, so truncation rate should be checked if the dataset changes. |
| dynamic padding | batch maximum | Pads only to the longest sequence in a batch (to a multiple of 8), saving compute and using GPU tensor cores efficiently. |

### QLoRA and memory parameters

| Parameter | Value | Purpose and reason for the choice |
|---|---:|---|
| `load_in_4bit` | `True` | Stores frozen base weights in 4-bit form, making 4B–8B models feasible on limited GPU memory. This makes the method QLoRA rather than ordinary LoRA. |
| quantization type | `nf4` | NF4 is designed for approximately normally distributed neural-network weights and is a standard QLoRA choice. |
| double quantization | `True` | Quantizes quantization constants too, reducing memory further with a small possible accuracy trade-off. |
| compute dtype | BF16, else FP16 | BF16 has a wider numerical range and is preferred on supported GPUs; FP16 supports older CUDA hardware. |
| gradient checkpointing | enabled | Recomputes some activations during backpropagation instead of storing them, saving memory at the cost of extra computation. |
| optimizer | `paged_adamw_8bit` | Lowers optimizer-state memory and uses paged memory management to handle temporary memory spikes. |
| `use_cache` | `False` | Disables the generation key/value cache, which is unnecessary for classification training and conflicts with gradient checkpointing. |

### LoRA parameters

| Parameter | Value | Purpose and reason for the choice |
|---|---:|---|
| `r` | 16 | Rank of each low-dimensional update. Rank 16 balances adapter capacity, memory, and speed. Larger ranks add trainable parameters and may learn more complex changes. |
| `lora_alpha` | 32 (`2 × r`) | Scales the LoRA update. With rank 16, the effective scale is `alpha/r = 2`. |
| `lora_dropout` | 0.05 | Randomly drops part of the adapter path during training to reduce overfitting. It is disabled during evaluation. |
| `bias` | `none` | Leaves base-model biases frozen, minimizing trainable parameters and adapter size. |
| target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj` | Adapts all main attention and MLP projections. This provides more capacity than attention-only LoRA for adapting language/noise representations and the classification task. |
| `modules_to_save` | `score` | The two-class classification head is newly initialized, so it must be fully trained and saved with the LoRA weights. |
| task type | `SEQ_CLS` | Tells PEFT that the downstream task is sequence classification, not causal generation. |

SinLlama exposes an `attn_only` option. It is `False`, so the same attention-plus-MLP target set is used. `True` would reduce memory and adapter size but also reduce adaptation capacity.

### Optimization parameters

| Parameter | Value | Purpose and reason for the choice |
|---|---:|---|
| learning rate | `1e-4` | Controls update size. It is higher than a typical full-model rate because only small adapters and the classification head are trained. |
| epochs | 1, 3, or 5 | Passes over training data: SinLlama uses 1, Llama/Qwen 7B use 3, and Qwen 4B uses 5. These are experiment-specific compute/capacity choices and should ultimately be justified using validation curves. |
| device batch size | 1 or 2 | Examples processed on one GPU at once. Qwen 7B uses 1 because the larger model needs more memory. |
| gradient accumulation | 16 or 32 | Sums gradients across micro-batches before updating. All four configurations have an effective single-GPU batch of 32 despite different memory needs. |
| scheduler | cosine | Reduces learning rate toward the end, allowing larger early changes and smaller late refinements. |
| `warmup_ratio` | 0.06 | Ramps learning rate during the first 6% of steps, reducing instability at the start. |
| `weight_decay` | 0.01 | Mild regularization discouraging unnecessarily large trained weights. |
| `max_grad_norm` | 0.3 | Clips large gradients to stabilize training. |
| `group_by_length` | `True` | Groups similarly sized examples to reduce padding and wasted compute. |

### Imbalance handling and model selection

For each training split, the loss weight for class `c` is:

```text
weight[c] = number_of_training_examples / (2 × number_of_examples_in_class_c)
```

The minority class therefore contributes more to cross-entropy loss. This matters because accuracy can look good even when a model rarely identifies `OFF` examples.

For the same reason, the best checkpoint is selected using **macro-F1**, not accuracy or training loss. Macro-F1 computes F1 separately for `NOT` and `OFF` and weights the classes equally. Reports also include balanced accuracy and per-class metrics so majority-class bias remains visible.

## 5. Decisions made in the experiment design

- **Parameter-efficient tuning instead of full fine-tuning.** Only LoRA matrices and the classification head are trained, reducing memory, runtime, storage, and the risk of overwriting general language knowledge.
- **QLoRA instead of unquantized LoRA.** Four-bit base weights make comparisons across 4B, 7B, and 8B models practical on limited hardware.
- **A classification head instead of generating `NOT` or `OFF`.** Direct logits avoid parsing generated text and provide a conventional supervised objective.
- **Separate adapters for separate noise conditions.** This supports a controlled train-condition × test-condition robustness matrix. Combining variants would answer a different question: performance of one noise-augmented model.
- **Paired data checks across conditions.** Matching IDs and labels ensure differences arise from text transformation, not different examples or ground truth.
- **No test-set feedback during training.** A 10% training split selects checkpoints; configured test sets are held for final evaluation.
- **Macro-F1 as the primary metric.** This treats both classes equally under label imbalance.
- **The same effective batch across model sizes.** Qwen 7B reduces its micro-batch from 2 to 1 and doubles accumulation, preserving an effective batch of 32 while fitting memory.
- **Attention and MLP projections are adapted.** This favors capacity over the smallest possible adapter because the task involves classification and script/noise adaptation.
- **Fixed seed and mostly common hyperparameters.** This improves comparability, but different epoch counts mean this is not a perfectly controlled model-size ablation.

These rationales are interpretations of the code. Unless supported by a recorded hyperparameter search, rank 16, learning rate `1e-4`, and the epoch counts should be described as chosen working settings, not proven optimal values.

## 6. What was actually completed for Qwen 4B

The saved run in `qwen4b/qwen4b/lora_results/train_transliteration_heavy_seed42/` confirms:

- 6,750 training and 750 validation examples;
- 5 epochs and 1,055 optimizer steps;
- learning rate `1e-4`, LoRA rank 16, and maximum length 128;
- best validation macro-F1 of approximately **0.8182** at epoch 5;
- test macro-F1 of approximately **0.7992** on heavy transliteration, **0.7979** on light transliteration, **0.4706** on clean text, **0.4792** on light code-mix, and **0.4807** on heavy code-mix.

This suggests strong transfer between transliteration severities but weak transfer to clean script and code-mixing. That conclusion is specific to this saved run, not a general claim about Qwen. Validation loss increased after epoch 2 while macro-F1 improved, suggesting increasingly confident errors and possible overfitting/calibration issues. A follow-up should compare epoch 2–5 checkpoints rather than relying on loss alone.

## 7. Outputs and how to read them

- `adapter/`: LoRA weights, adapter configuration, and tokenizer files
- `checkpoints/` or `ckpt/`: resumable trainer checkpoints
- `run_summary.json`: configuration, dataset sizes, training summary, and test metrics
- `metrics.csv` / `all_metrics.csv`: metrics for individual or all pairings
- `predictions.jsonl` / `all_predictions.jsonl`: example-level outputs for error analysis
- `macro_f1_matrix.csv/.png`: training conditions on rows and test conditions on columns

Use macro-F1 as the headline measure, but inspect `OFF` recall and prediction files too. A useful hate-speech detector should not obtain a good aggregate score merely by favoring `NOT`.

## 8. Recommended follow-up experiments

For stronger conclusions, run every model on the same training conditions, retain the same test conditions, and repeat each configuration with several seeds; report mean and standard deviation. Useful ablations include attention-only versus attention-plus-MLP LoRA, rank 8/16/32, one mixed-condition adapter versus separate adapters, and checkpoint/epoch selection using validation macro-F1. Record GPU type, library versions, wall-clock time, peak memory, and exact data revision for better reproducibility.
