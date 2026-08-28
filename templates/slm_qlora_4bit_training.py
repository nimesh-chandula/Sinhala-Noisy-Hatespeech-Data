#!/usr/bin/env python3
# Converted from slm_qlora_4bit_training.ipynb
# Run from the repository root: python templates/slm_qlora_4bit_training.py


# ============================================================================
# # SLM QLoRA Training for Sinhala Hate/Offensive Speech
# 
# Template for 4-bit QLoRA fine-tuning across the same SLMs used in `slm_classification_head_training.ipynb`. Configure one training dataset, choose one or more test datasets, and run the selected models.
# ============================================================================


# ============================================================================
# ## 1. Install dependencies
# ============================================================================


# %% [code cell 2]
# Notebook dependency install skipped in script. Install once before running:
#   python -m pip install -q -U "transformers>=4.45" "peft>=0.13" "accelerate>=1.0" "bitsandbytes>=0.46" "datasets>=3.0" pandas scikit-learn matplotlib seaborn huggingface_hub


# ============================================================================
# ## 2. Configuration
# ============================================================================


# %% [code cell 4]
from pathlib import Path
import dataclasses
import gc
import inspect
import json
import os
import time

import numpy as np
import pandas as pd
import torch

try:
    from IPython.display import display
except ImportError:
    def display(value):
        print(value.to_string() if hasattr(value, "to_string") else value)

SEED = 42
NUM_LABELS = 2
LABEL_NAME = {0: "NOT", 1: "OFF"}
LABEL2ID = {v: k for k, v in LABEL_NAME.items()}

# Set to a concrete data directory if auto-detection cannot find this repo's data folder.
DATA_ROOT = None
OUTPUT_ROOT = Path("benchmark_results/qlora_4bit")

# Dataset variants used by this template. Add custom JSONL files here if needed.
DATASETS = {
    "clean": {"train": Path("sold/train.jsonl"), "test": Path("sold/test.jsonl")},
    "codemix_light": {"train": Path("outputs/train/codemix_light.jsonl"), "test": Path("outputs/test/codemix_light.jsonl")},
    "codemix_heavy": {"train": Path("outputs/train/codemix_heavy.jsonl"), "test": Path("outputs/test/codemix_heavy.jsonl")},
    "transliteration_light": {"train": Path("outputs/train/transliteration_light.jsonl"), "test": Path("outputs/test/transliteration_light.jsonl")},
    "transliteration_heavy": {"train": Path("outputs/train/transliteration_heavy.jsonl"), "test": Path("outputs/test/transliteration_heavy.jsonl")},
    "compound_light": {"test": Path("outputs/test/compound_light.jsonl")},
    "compound_heavy": {"train": Path("outputs/train/compound_heavy.jsonl"), "test": Path("outputs/test/compound_heavy.jsonl")},
    "misspell_light": {"test": Path("outputs/test/misspell_light.jsonl")},
    "misspell_heavy": {"train": Path("outputs/train/misspell_heavy.jsonl"), "test": Path("outputs/test/misspell_heavy.jsonl")},
}

DATASET_ALIASES = {
    "codemix": "codemix_heavy",
    "transliteration": "transliteration_heavy",
    "compound": "compound_heavy",
    "misspell": "misspell_heavy",
}

# Train on one dataset and evaluate on multiple datasets.
# You may put more than one item in TRAIN_DATASETS to run several independent training jobs.

# "clean", "codemix_heavy", "transliteration_heavy","compound_heavy", "misspell_heavy"

TRAIN_DATASETS = ["clean"]
TEST_DATASETS = ["clean", "codemix_heavy", "transliteration_heavy","compound_heavy", "misspell_heavy"]
TRAIN_SUBSET = None  # e.g. 200 for a smoke test

TRAIN_DATASETS = [DATASET_ALIASES.get(name, name) for name in TRAIN_DATASETS]
TEST_DATASETS = [DATASET_ALIASES.get(name, name) for name in TEST_DATASETS]

# Change ACTIVE_MODELS assigned to you and change TRAIN_DATASETS array if you want to change train
# datasets. You can also change TEST_DATASETS array if you want to change test datasets. 
print("Datasets:", TRAIN_DATASETS, "->", TEST_DATASETS)

# Naveen - Sinllama
# Sansala - Qwen/Qwen3-4B,
# Dulakshi - Qwen/Qwen3-8B,
# Janodi - meta-llama/Llama-3.2-3B,meta-llama/Llama-3.1-8B

# Llama repositories are gated on Hugging Face. Use Qwen defaults unless your
# HF account has approved access for the selected gated model.
MODELS = {
    "qwen_4b": "Qwen/Qwen3-4B",
    "qwen_8b": "Qwen/Qwen3-8B",
    "llama_3b_gated": "meta-llama/Llama-3.2-3B",
    "llama_8b_gated": "meta-llama/Llama-3.1-8B",
    "sinllama_gated": "polyglots/SinLlama_v01",
}

# Change ACTIVE_MODELS assigned to you and change TRAIN_DATASETS / TEST_DATASETS above.
# Naveen - SinLlama
# Sansala - Qwen/Qwen3-4B
# Dulakshi - Qwen/Qwen3-8B
# Janodi - meta-llama/Llama-3.2-3B, meta-llama/Llama-3.1-8B
ACTIVE_MODELS = ["sinllama_gated"]  # Ungated default. Use "llama_3b_gated" only after HF access is approved.

EPOCHS = 3.0
LEARNING_RATE = 2e-4
TRAIN_BATCH_SIZE = 8
EVAL_BATCH_SIZE = 8
GRADIENT_ACCUMULATION_STEPS = 4
MAX_LENGTH = 128
WEIGHT_DECAY = 0.01
VALIDATION_FRACTION = 0.10
LOGGING_STEPS = 10

LORA_R = 16
LORA_ALPHA = 2 * LORA_R
LORA_DROPOUT = 0.05
LORA_TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
LORA_MODULES_TO_SAVE = ["score", "classifier", "classification_head"]

np.random.seed(SEED)
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

print("torch", torch.__version__, "| CUDA", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise RuntimeError("QLoRA training requires a CUDA GPU with bitsandbytes support.")
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    print(f"cuda:{i} {props.name}, {props.total_memory / 2**30:.1f} GiB")


# ============================================================================
# ## 3. Authenticate and locate data
# ============================================================================


# %% [code cell 6]
from huggingface_hub import login

hf_token = os.environ.get("HF_TOKEN")

if hf_token:
    login(token=hf_token, add_to_git_credential=False)
    print("Authenticated from HF_TOKEN.")
else:
    print("HF_TOKEN is not set. Ungated models will still work; gated models require an approved token.")

unknown_datasets = (set(TRAIN_DATASETS) | set(TEST_DATASETS)) - set(DATASETS)
unknown_models = set(ACTIVE_MODELS) - set(MODELS)
if unknown_datasets:
    raise KeyError(f"Undefined dataset names: {sorted(unknown_datasets)}")
if unknown_models:
    raise KeyError(f"Undefined model names: {sorted(unknown_models)}")
if not TRAIN_DATASETS or not TEST_DATASETS:
    raise ValueError("TRAIN_DATASETS and TEST_DATASETS must both be non-empty.")

required_paths = []
for name in TRAIN_DATASETS:
    required_paths.append(DATASETS[name]["train"])
for name in TEST_DATASETS:
    required_paths.append(DATASETS[name]["test"])

def is_data_root(path):
    path = Path(path)
    return all((path / rel).is_file() for rel in required_paths)

def find_data_root(explicit=None):
    if explicit is not None:
        explicit = Path(explicit)
        if not is_data_root(explicit):
            raise FileNotFoundError(f"Selected files were not found below DATA_ROOT: {explicit.resolve()}")
        return explicit
    cwd = Path.cwd().resolve()
    for parent in (cwd, *cwd.parents):
        for candidate in (parent / "data", parent):
            if is_data_root(candidate):
                return candidate
    kaggle = Path("/kaggle/input")
    if kaggle.exists():
        for candidate in kaggle.iterdir():
            if candidate.is_dir() and is_data_root(candidate):
                return candidate
    raise FileNotFoundError("Could not locate all selected files. Set DATA_ROOT explicitly.")

DATA_ROOT = find_data_root(DATA_ROOT)
FILES = {}
for name in TRAIN_DATASETS:
    FILES[f"{name}_train"] = DATA_ROOT / DATASETS[name]["train"]
for name in TEST_DATASETS:
    FILES[f"{name}_test"] = DATA_ROOT / DATASETS[name]["test"]

print("DATA_ROOT =", DATA_ROOT.resolve())
display(pd.DataFrame([{"key": key, "path": str(path)} for key, path in FILES.items()]))


# ============================================================================
# ## 4. Load and validate datasets
# ============================================================================


# %% [code cell 8]
def read_jsonl(path):
    records = []
    with Path(path).open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path}, line {line_number}: {exc}") from exc
    if not records:
        raise ValueError(f"Dataset is empty: {path}")
    return pd.DataFrame(records)

def normalize_label_series(labels):
    mapping = {
        "0": 0, "1": 1,
        "NOT": 0, "OFF": 1,
        "not": 0, "off": 1,
        "negative": 0, "positive": 1,
        "not-offensive": 0, "offensive": 1,
        "non-hate": 0, "hate": 1,
    }
    normalized = labels.astype(str).str.strip().map(mapping)
    if normalized.isna().any():
        bad = sorted(labels[normalized.isna()].astype(str).unique().tolist())
        raise ValueError(f"Unmapped labels: {bad}")
    return normalized.astype(int)

def canonicalize(df, condition, split):
    id_candidates = ("post_id", "source_id", "id", "sentence_id", "orig_id")
    text_candidates = ("text", "noisy_text", "transliterated", "transliteration", "romanized")
    id_col = next((col for col in id_candidates if col in df.columns), None)
    text_col = next((col for col in text_candidates if col in df.columns), None)
    if id_col is None or text_col is None or "label" not in df.columns:
        raise KeyError(f"{condition}_{split}: unsupported columns {df.columns.tolist()}")
    out = df[[id_col, text_col, "label"]].rename(columns={id_col: "id", text_col: "text"}).copy()
    out["id"] = out["id"].astype(str)
    out["text"] = out["text"].astype(str)
    out["label"] = normalize_label_series(out["label"])
    if out["id"].duplicated().any():
        raise ValueError(f"{condition}_{split}: duplicate IDs found")
    if out["text"].str.strip().eq("").any():
        raise ValueError(f"{condition}_{split}: empty text found")
    out["condition"] = condition
    out["split"] = split
    return out

frames = {}
for key, path in FILES.items():
    condition, split = key.rsplit("_", 1)
    frames[key] = canonicalize(read_jsonl(path), condition, split)
    counts = frames[key]["label"].value_counts().sort_index().to_dict()
    print(f"{key:32s} n={len(frames[key]):5d} labels={counts}")

# Verify labels when selected datasets are aligned by ID.
for split, names in (("train", TRAIN_DATASETS), ("test", TEST_DATASETS)):
    split_frames = {name: frames[f"{name}_{split}"].set_index("id") for name in names}
    for left_index, left_name in enumerate(names):
        for right_name in names[left_index + 1:]:
            left, right = split_frames[left_name], split_frames[right_name]
            if set(left.index) == set(right.index):
                right = right.loc[left.index]
                if not np.array_equal(left["label"].to_numpy(), right["label"].to_numpy()):
                    raise ValueError(f"Label mismatch between aligned {left_name} and {right_name} {split} data")

preview = []
for name in TEST_DATASETS:
    row = frames[f"{name}_test"].head(1).copy()
    row["dataset"] = name
    preview.append(row[["dataset", "id", "text", "label"]])
display(pd.concat(preview, ignore_index=True).assign(label_name=lambda df: df["label"].map(LABEL_NAME)))


# ============================================================================
# ## 5. Tokenizer, 4-bit QLoRA model, and datasets
# ============================================================================


# %% [code cell 10]
from datasets import ClassLabel, Dataset
from huggingface_hub.errors import GatedRepoError
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorWithPadding,
    set_seed,
)

COMPUTE_DTYPE = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16

def explain_gated_model_error(model_id, exc):
    raise RuntimeError(
        f"Cannot access gated Hugging Face model '{model_id}'. "
        "Either request access on the model page and set HF_TOKEN to an approved token, "
        "or choose an ungated key such as 'qwen_4b' in ACTIVE_MODELS."
    ) from exc

def build_tokenizer(model_id):
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_id, trust_remote_code=True, use_fast=True)
    except (GatedRepoError, OSError) as exc:
        if "gated repo" in str(exc).lower() or "restricted" in str(exc).lower():
            explain_gated_model_error(model_id, exc)
        raise
    tokenizer.padding_side = "right"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer

def make_dataset(frame, tokenizer):
    dataset = Dataset.from_pandas(frame[["id", "text", "label"]], preserve_index=False)
    dataset = dataset.cast_column("label", ClassLabel(names=["NOT", "OFF"]))
    return dataset.map(
        lambda batch: tokenizer(batch["text"], truncation=True, max_length=MAX_LENGTH),
        batched=True,
        remove_columns=["text"],
    )

def from_pretrained_dtype_kwargs(dtype):
    params = inspect.signature(AutoModelForSequenceClassification.from_pretrained).parameters
    if "dtype" in params:
        return {"dtype": dtype}
    return {"torch_dtype": dtype}

def present_module_roots(model):
    roots = set()
    for name, _module in model.named_modules():
        leaf = name.rsplit(".", 1)[-1]
        roots.add(leaf)
    return roots

def build_model(model_id, tokenizer):
    quantization = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_use_double_quant=True,
        bnb_4bit_compute_dtype=COMPUTE_DTYPE,
    )
    model_kwargs = dict(
        num_labels=NUM_LABELS,
        id2label=LABEL_NAME,
        label2id=LABEL2ID,
        pad_token_id=tokenizer.pad_token_id,
        quantization_config=quantization,
        device_map="auto",
        trust_remote_code=True,
        low_cpu_mem_usage=True,
        attn_implementation="sdpa",
        **from_pretrained_dtype_kwargs(COMPUTE_DTYPE),
    )
    try:
        model = AutoModelForSequenceClassification.from_pretrained(model_id, **model_kwargs)
    except (GatedRepoError, OSError) as exc:
        if "gated repo" in str(exc).lower() or "restricted" in str(exc).lower():
            explain_gated_model_error(model_id, exc)
        raise

    if model.config.pad_token_id is None:
        model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False

    model = prepare_model_for_kbit_training(
        model,
        use_gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
    )
    model.enable_input_require_grads()

    module_roots = present_module_roots(model)
    target_modules = [name for name in LORA_TARGET_MODULES if name in module_roots]
    modules_to_save = [name for name in LORA_MODULES_TO_SAVE if name in module_roots]
    if not target_modules:
        raise RuntimeError(
            f"No LoRA target modules found for {model_id}. "
            f"Available module leaves include: {sorted(module_roots)[:80]}"
        )
    if not modules_to_save:
        print("No explicit sequence-classification head matched LORA_MODULES_TO_SAVE; PEFT will use its default handling.")
        modules_to_save = None

    print("LoRA target_modules:", target_modules)
    print("LoRA modules_to_save:", modules_to_save)
    model = get_peft_model(model, LoraConfig(
        task_type="SEQ_CLS",
        r=LORA_R,
        lora_alpha=LORA_ALPHA,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        target_modules=target_modules,
        modules_to_save=modules_to_save,
    ))
    model.print_trainable_parameters()
    return model


# ============================================================================
# ## 6. Metrics and trainer
# ============================================================================


# %% [code cell 12]
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    f1_score,
    precision_recall_fscore_support,
)
from transformers import Trainer, TrainingArguments

def metric_values(labels, predictions):
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, predictions, labels=[0, 1], zero_division=0
    )
    return {
        "accuracy": accuracy_score(labels, predictions),
        "balanced_accuracy": balanced_accuracy_score(labels, predictions),
        "macro_f1": f1_score(labels, predictions, average="macro", zero_division=0),
        "not_precision": precision[0], "not_recall": recall[0], "not_f1": f1[0],
        "off_precision": precision[1], "off_recall": recall[1], "off_f1": f1[1],
    }

def compute_metrics(eval_prediction):
    logits, labels = eval_prediction
    return metric_values(labels, np.argmax(logits, axis=-1))

def trainer_tokenizer_kwargs(tokenizer):
    parameters = inspect.signature(Trainer.__init__).parameters
    if "processing_class" in parameters:
        return {"processing_class": tokenizer}
    if "tokenizer" in parameters:
        return {"tokenizer": tokenizer}
    return {}

class WeightedTrainer(Trainer):
    def __init__(self, class_weights=None, **kwargs):
        super().__init__(**kwargs)
        self.class_weights = class_weights

    def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
        labels = inputs.pop("labels")
        outputs = model(**inputs)
        weights = self.class_weights.to(outputs.logits.device, outputs.logits.dtype)
        loss = nn.CrossEntropyLoss(weight=weights)(outputs.logits, labels)
        return (loss, outputs) if return_outputs else loss

def make_class_weights(labels):
    counts = np.bincount(np.asarray(labels), minlength=NUM_LABELS)
    if (counts == 0).any():
        raise ValueError(f"Both classes must appear in the training split. Counts: {counts.tolist()}")
    weights = counts.sum() / (NUM_LABELS * counts)
    return torch.tensor(weights, dtype=torch.float32)

def training_arguments(output_dir):
    kwargs = dict(
        output_dir=str(output_dir / "checkpoints"),
        seed=SEED,
        num_train_epochs=EPOCHS,
        per_device_train_batch_size=TRAIN_BATCH_SIZE,
        per_device_eval_batch_size=EVAL_BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION_STEPS,
        eval_accumulation_steps=8,
        learning_rate=LEARNING_RATE,
        lr_scheduler_type="cosine",
        warmup_ratio=0.06,
        weight_decay=WEIGHT_DECAY,
        max_grad_norm=0.3,
        fp16=COMPUTE_DTYPE == torch.float16,
        bf16=COMPUTE_DTYPE == torch.bfloat16,
        optim="paged_adamw_8bit",
        gradient_checkpointing=True,
        gradient_checkpointing_kwargs={"use_reentrant": False},
        logging_steps=LOGGING_STEPS,
        eval_strategy="epoch",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        greater_is_better=True,
        report_to="none",
        dataloader_num_workers=2,
        dataloader_pin_memory=False,
        group_by_length=True,
        label_names=["labels"],
    )
    valid = {field.name for field in dataclasses.fields(TrainingArguments)}
    return TrainingArguments(**{key: value for key, value in kwargs.items() if key in valid})


# ============================================================================
# ## 7. Run one model/training-dataset experiment
# ============================================================================


# %% [code cell 14]
def evaluate_dataset(trainer, dataset, frame, model_name, model_id, train_condition, test_condition, output_dir):
    prediction_output = trainer.predict(dataset)
    predictions = np.argmax(prediction_output.predictions, axis=-1)
    labels = prediction_output.label_ids
    metrics = metric_values(labels, predictions)
    report = classification_report(
        labels,
        predictions,
        labels=[0, 1],
        target_names=[LABEL_NAME[0], LABEL_NAME[1]],
        zero_division=0,
        output_dict=True,
    )
    result = {
        "model": model_name,
        "model_id": model_id,
        "train_dataset": train_condition,
        "test_dataset": test_condition,
        "num_test_samples": len(dataset),
        **metrics,
    }
    predictions_frame = pd.DataFrame({
        "id": frame["id"].to_numpy(),
        "model": model_name,
        "train_dataset": train_condition,
        "test_dataset": test_condition,
        "label": labels,
        "prediction": predictions,
        "text": frame["text"].to_numpy(),
    })
    with (output_dir / f"{test_condition}_classification_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return result, predictions_frame

def run_experiment(model_name, train_condition):
    model_id = MODELS[model_name]

    print("\n" + "=" * 80)
    print(f"MODEL: {model_name} | TRAIN: {train_condition} | METHOD: 4-bit QLoRA")
    print("=" * 80)

    set_seed(SEED)
    output_dir = OUTPUT_ROOT / model_name / f"train_{train_condition}_seed{SEED}"
    output_dir.mkdir(parents=True, exist_ok=True)

    train_frame = frames[f"{train_condition}_train"].copy()
    if TRAIN_SUBSET is not None:
        train_frame = train_frame.sample(n=min(TRAIN_SUBSET, len(train_frame)), random_state=SEED).reset_index(drop=True)

    tokenizer = build_tokenizer(model_id)
    full_train = make_dataset(train_frame, tokenizer)
    split = full_train.train_test_split(
        test_size=VALIDATION_FRACTION,
        seed=SEED,
        stratify_by_column="label",
    )
    train_ds, validation_ds = split["train"], split["test"]
    class_weights = make_class_weights(train_ds["label"])
    print(f"train={len(train_ds)}, validation={len(validation_ds)}, class_weights={class_weights.tolist()}")

    model = build_model(model_id, tokenizer)
    trainer = WeightedTrainer(
        model=model,
        args=training_arguments(output_dir),
        train_dataset=train_ds,
        eval_dataset=validation_ds,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer, pad_to_multiple_of=8),
        compute_metrics=compute_metrics,
        class_weights=class_weights,
        **trainer_tokenizer_kwargs(tokenizer),
    )

    started = time.time()
    train_result = trainer.train()
    trainer.model.save_pretrained(output_dir / "adapter")
    tokenizer.save_pretrained(output_dir / "adapter")

    result_rows = []
    prediction_frames = []
    for test_condition in TEST_DATASETS:
        test_frame = frames[f"{test_condition}_test"].copy()
        test_ds = make_dataset(test_frame, tokenizer)
        result, predictions = evaluate_dataset(
            trainer, test_ds, test_frame, model_name, model_id, train_condition, test_condition, output_dir
        )
        result["num_train_samples"] = len(train_ds)
        result["num_validation_samples"] = len(validation_ds)
        result["elapsed_hours"] = (time.time() - started) / 3600
        result_rows.append(result)
        prediction_frames.append(predictions)
        print(f"{test_condition:24s} macro_f1={result['macro_f1']:.4f} accuracy={result['accuracy']:.4f}")

    results = pd.DataFrame(result_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    results.to_csv(output_dir / "metrics.csv", index=False)
    predictions.to_json(output_dir / "predictions.jsonl", orient="records", lines=True, force_ascii=False)
    with (output_dir / "run_summary.json").open("w", encoding="utf-8") as handle:
        json.dump({
            "model": model_name,
            "model_id": model_id,
            "train_condition": train_condition,
            "test_conditions": TEST_DATASETS,
            "seed": SEED,
            "epochs": EPOCHS,
            "learning_rate": LEARNING_RATE,
            "max_length": MAX_LENGTH,
            "fine_tuning_method": "qlora_4bit",
            "quantization": {
                "load_in_4bit": True,
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_use_double_quant": True,
                "bnb_4bit_compute_dtype": str(COMPUTE_DTYPE),
            },
            "lora": {
                "r": LORA_R,
                "alpha": LORA_ALPHA,
                "dropout": LORA_DROPOUT,
                "target_modules": LORA_TARGET_MODULES,
                "modules_to_save": LORA_MODULES_TO_SAVE,
            },
            "train_metrics": train_result.metrics,
        }, handle, indent=2, default=float)

    del trainer, model, tokenizer, train_ds, validation_ds, full_train
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return results, predictions


# ============================================================================
# ## 8. Run configured benchmark
# ============================================================================


# %% [code cell 16]
all_results = []
all_predictions = []
started = time.time()

for model_name in ACTIVE_MODELS:
    for train_condition in TRAIN_DATASETS:
        results, predictions = run_experiment(model_name, train_condition)
        all_results.append(results)
        all_predictions.append(predictions)

        partial_results = pd.concat(all_results, ignore_index=True)
        partial_results.to_csv(OUTPUT_ROOT / "benchmark_summary_partial.csv", index=False)

results = pd.concat(all_results, ignore_index=True)
predictions = pd.concat(all_predictions, ignore_index=True)
results.to_csv(OUTPUT_ROOT / "benchmark_summary.csv", index=False)
predictions.to_json(OUTPUT_ROOT / "all_predictions.jsonl", orient="records", lines=True, force_ascii=False)

matrix = results.pivot_table(index=["model", "train_dataset"], columns="test_dataset", values="macro_f1")
matrix.to_csv(OUTPUT_ROOT / "macro_f1_matrix.csv")
display(results.round(4))
display(matrix.round(4))
print(f"Finished in {(time.time() - started) / 3600:.2f} hours")
print("Artifacts:", OUTPUT_ROOT.resolve())


# ============================================================================
# ## 9. Plot macro-F1 matrix
# ============================================================================


# %% [code cell 18]
import matplotlib.pyplot as plt
import seaborn as sns

plot_matrix = matrix.reindex(columns=TEST_DATASETS)
plt.figure(figsize=(10, max(3, 0.45 * len(plot_matrix))))
sns.heatmap(plot_matrix, annot=True, fmt=".4f", cmap="Blues", vmin=0, vmax=1)
plt.title("4-bit QLoRA macro-F1")
plt.xlabel("Test dataset")
plt.ylabel("Model / training dataset")
plt.tight_layout()
plt.savefig(OUTPUT_ROOT / "macro_f1_matrix.png", dpi=180, bbox_inches="tight")
plt.show()


# ============================================================================
# ## Reporting checklist
# 
# - Record `ACTIVE_MODELS`, `TRAIN_DATASETS`, `TEST_DATASETS`, and every changed hyperparameter.
# - Report macro-F1, balanced accuracy, OFF F1, and NOT F1 from `benchmark_summary.csv`.
# - Include `macro_f1_matrix.png` for the cross-dataset robustness view.
# - Mention that models were loaded with 4-bit NF4 quantization and trained with QLoRA adapters.
# ============================================================================

