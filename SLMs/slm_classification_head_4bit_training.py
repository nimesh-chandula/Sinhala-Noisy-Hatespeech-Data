#!/usr/bin/env python3
# Train only the sequence-classification head on a 4-bit loaded SLM.
# Run from the repository root:
#   python3 templates/slm_classification_head_4bit_training.py

from pathlib import Path
import gc
import json
import os
import time

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from datasets import ClassLabel, Dataset
from huggingface_hub import get_token, login
from huggingface_hub.errors import GatedRepoError
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    f1_score,
    precision_recall_fscore_support,
)
from torch.utils.data import DataLoader
from tqdm.auto import tqdm
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorWithPadding,
    get_cosine_schedule_with_warmup,
    set_seed,
)

SEED = 42
NUM_LABELS = 2
LABEL_NAME = {0: "NOT", 1: "OFF"}
LABEL2ID = {v: k for k, v in LABEL_NAME.items()}

# Set to a concrete data directory if auto-detection cannot find this repo's data folder.
DATA_ROOT = None
OUTPUT_ROOT = Path("benchmark_results/classification_head_4bit")

# Dataset variants copied from slm_qlora_4bit_training.py. Keep these as-is for
# the same clean/noisy benchmark setup.
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
# "clean", "codemix_heavy", "transliteration_heavy"

TRAIN_DATASETS = ["compound_heavy"]
TEST_DATASETS = [ "clean", "codemix_heavy", "transliteration_heavy","compound_heavy", "misspell_heavy"]
TRAIN_SUBSET = None  # e.g. 200 for a smoke test

MODELS = {
    "qwen_4b": "Qwen/Qwen3-4B",
    "qwen_8b": "Qwen/Qwen3-8B",
    "llama_3b_gated": "meta-llama/Llama-3.2-3B",
    "llama_8b_gated": "meta-llama/Llama-3.1-8B",
    "sinllama_gated": "polyglots/SinLlama_v01",
}

ACTIVE_MODELS = ["llama_3b_gated"]

# Hyperparameters copied from slm_qlora_4bit_training.py.
EPOCHS = 3.0
LEARNING_RATE = 2e-4
TRAIN_BATCH_SIZE = 8
EVAL_BATCH_SIZE = 8
GRADIENT_ACCUMULATION_STEPS = 4
MAX_LENGTH = 128
WEIGHT_DECAY = 0.01
VALIDATION_FRACTION = 0.10
LOGGING_STEPS = 10
EVAL_ACCUMULATION_STEPS = 8
WARMUP_RATIO = 0.06
MAX_GRAD_NORM = 0.3
OPTIMIZER = "paged_adamw_8bit"

np.random.seed(SEED)
OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)

print("Datasets:", TRAIN_DATASETS, "->", TEST_DATASETS)
print("torch", torch.__version__, "| CUDA", torch.cuda.is_available())
if not torch.cuda.is_available():
    raise RuntimeError("4-bit training requires a CUDA GPU with bitsandbytes support.")
for i in range(torch.cuda.device_count()):
    props = torch.cuda.get_device_properties(i)
    print(f"cuda:{i} {props.name}, {props.total_memory / 2**30:.1f} GiB")

hf_token = os.environ.get("HF_TOKEN") or get_token()
HF_AUTH_KWARGS = {"token": hf_token} if hf_token else {}
if os.environ.get("HF_TOKEN"):
    login(token=hf_token, add_to_git_credential=False)
    print("Authenticated from HF_TOKEN.")
elif hf_token:
    print("Authenticated from the Hugging Face token cache.")
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
print(pd.DataFrame([{"key": key, "path": str(path)} for key, path in FILES.items()]).to_string(index=False))


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

for split, names in (("train", TRAIN_DATASETS), ("test", TEST_DATASETS)):
    split_frames = {name: frames[f"{name}_{split}"].set_index("id") for name in names}
    for left_index, left_name in enumerate(names):
        for right_name in names[left_index + 1:]:
            left, right = split_frames[left_name], split_frames[right_name]
            if set(left.index) == set(right.index):
                right = right.loc[left.index]
                if not np.array_equal(left["label"].to_numpy(), right["label"].to_numpy()):
                    raise ValueError(f"Label mismatch between aligned {left_name} and {right_name} {split} data")


COMPUTE_DTYPE = torch.bfloat16 if torch.cuda.is_available() and torch.cuda.is_bf16_supported() else torch.float16


def explain_gated_model_error(model_id, exc):
    auth_status = (
        "A Hugging Face token was found, but this account/token is not approved for that model. "
        if hf_token else
        "No Hugging Face token was found. "
    )
    raise RuntimeError(
        f"Cannot access gated Hugging Face model '{model_id}'. "
        f"{auth_status}"
        "Request access on the model page and set HF_TOKEN to an approved token, "
        "or choose an ungated key such as 'qwen_4b' in ACTIVE_MODELS."
    ) from exc


def build_tokenizer(model_id):
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            use_fast=True,
            **HF_AUTH_KWARGS,
        )
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


def set_trainable_classification_head(model):
    for parameter in model.parameters():
        parameter.requires_grad = False

    head_markers = ("score", "classifier", "classification_head")
    trainable_names = []
    for name, parameter in model.named_parameters():
        if any(marker in name for marker in head_markers):
            parameter.requires_grad = True
            trainable_names.append(name)
            print("TRAINABLE:", name, tuple(parameter.shape), parameter.dtype)

    if not trainable_names:
        print("No head was found automatically. Candidate parameter names:")
        for name, parameter in model.named_parameters():
            print(name, tuple(parameter.shape), parameter.dtype)
        raise RuntimeError("Modify head_markers in set_trainable_classification_head for this model.")

    total = sum(parameter.numel() for parameter in model.parameters())
    trainable = sum(parameter.numel() for parameter in model.parameters() if parameter.requires_grad)
    print(f"Total parameters:     {total:,}")
    print(f"Trainable parameters: {trainable:,} ({100 * trainable / total:.6f}%)")
    return trainable_names


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
        torch_dtype=COMPUTE_DTYPE,
        **HF_AUTH_KWARGS,
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
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    return model, set_trainable_classification_head(model)


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


def make_class_weights(labels):
    counts = np.bincount(np.asarray(labels), minlength=NUM_LABELS)
    if (counts == 0).any():
        raise ValueError(f"Both classes must appear in the training split. Counts: {counts.tolist()}")
    weights = counts.sum() / (NUM_LABELS * counts)
    return torch.tensor(weights, dtype=torch.float32)


def make_loader(dataset, tokenizer, batch_size, shuffle):
    dataset = dataset.remove_columns([name for name in ("id",) if name in dataset.column_names])
    dataset = dataset.rename_column("label", "labels")
    dataset.set_format(type="torch")
    generator = torch.Generator()
    generator.manual_seed(SEED)
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        generator=generator if shuffle else None,
        collate_fn=DataCollatorWithPadding(tokenizer=tokenizer, pad_to_multiple_of=8),
        num_workers=2,
        pin_memory=False,
    )


def build_optimizer(trainable_parameters):
    if OPTIMIZER != "paged_adamw_8bit":
        raise ValueError(f"This script preserves the QLoRA optimizer hyperparameter. Unsupported OPTIMIZER={OPTIMIZER!r}")
    try:
        import bitsandbytes as bnb
    except ImportError as exc:
        raise ImportError("bitsandbytes is required for OPTIMIZER='paged_adamw_8bit'.") from exc
    return bnb.optim.PagedAdamW8bit(trainable_parameters, lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)


def evaluate_model(model, loader, class_weights=None):
    model.eval()
    losses = []
    all_labels = []
    all_predictions = []
    loss_fn = None
    if class_weights is not None:
        loss_fn = nn.CrossEntropyLoss(weight=class_weights.to(model.device))

    with torch.no_grad():
        for batch in loader:
            labels = batch.pop("labels").to(model.device)
            batch = {key: value.to(model.device) for key, value in batch.items()}
            outputs = model(**batch)
            logits = outputs.logits
            if loss_fn is not None:
                losses.append(loss_fn(logits.float(), labels).detach().cpu().item())
            all_labels.append(labels.detach().cpu().numpy())
            all_predictions.append(torch.argmax(logits, dim=-1).detach().cpu().numpy())

    labels = np.concatenate(all_labels)
    predictions = np.concatenate(all_predictions)
    metrics = metric_values(labels, predictions)
    if losses:
        metrics["loss"] = float(np.mean(losses))
    return metrics, labels, predictions


def train_head(model, train_loader, validation_loader, output_dir, class_weights):
    trainable_parameters = [parameter for parameter in model.parameters() if parameter.requires_grad]
    optimizer = build_optimizer(trainable_parameters)

    update_steps_per_epoch = int(np.ceil(len(train_loader) / GRADIENT_ACCUMULATION_STEPS))
    max_train_steps = int(np.ceil(EPOCHS * update_steps_per_epoch))
    warmup_steps = int(WARMUP_RATIO * max_train_steps)
    scheduler = get_cosine_schedule_with_warmup(
        optimizer,
        num_warmup_steps=warmup_steps,
        num_training_steps=max_train_steps,
    )
    class_weights = class_weights.to(model.device)
    loss_fn = nn.CrossEntropyLoss(weight=class_weights)
    scaler = torch.cuda.amp.GradScaler(enabled=COMPUTE_DTYPE == torch.float16)

    best_macro_f1 = -1.0
    best_state = None
    global_step = 0
    completed_steps = 0
    train_history = []

    model.train()
    optimizer.zero_grad(set_to_none=True)
    total_epochs = int(np.ceil(EPOCHS))
    for epoch in range(total_epochs):
        if epoch >= EPOCHS:
            break
        progress = tqdm(train_loader, desc=f"epoch {epoch + 1}/{total_epochs}", leave=False)
        running_loss = 0.0
        for step, batch in enumerate(progress, start=1):
            labels = batch.pop("labels").to(model.device)
            batch = {key: value.to(model.device) for key, value in batch.items()}

            with torch.autocast(device_type="cuda", dtype=COMPUTE_DTYPE):
                outputs = model(**batch)
                loss = loss_fn(outputs.logits.float(), labels)
                loss_for_backward = loss / GRADIENT_ACCUMULATION_STEPS

            scaler.scale(loss_for_backward).backward()
            running_loss += loss.detach().float().item()
            do_update = step % GRADIENT_ACCUMULATION_STEPS == 0 or step == len(train_loader)
            if do_update:
                scaler.unscale_(optimizer)
                torch.nn.utils.clip_grad_norm_(trainable_parameters, MAX_GRAD_NORM)
                scaler.step(optimizer)
                scaler.update()
                scheduler.step()
                optimizer.zero_grad(set_to_none=True)
                completed_steps += 1

            global_step += 1
            if global_step % LOGGING_STEPS == 0:
                progress.set_postfix(loss=f"{running_loss / step:.4f}", lr=f"{scheduler.get_last_lr()[0]:.2e}")

        validation_metrics, _, _ = evaluate_model(model, validation_loader, class_weights=class_weights)
        validation_macro_f1 = validation_metrics["macro_f1"]
        train_history.append({
            "epoch": epoch + 1,
            "train_loss": running_loss / max(1, len(train_loader)),
            **{f"validation_{key}": value for key, value in validation_metrics.items()},
        })
        print(
            f"epoch={epoch + 1} train_loss={running_loss / max(1, len(train_loader)):.4f} "
            f"validation_macro_f1={validation_macro_f1:.4f}"
        )
        if validation_macro_f1 > best_macro_f1:
            best_macro_f1 = validation_macro_f1
            best_state = {
                name: parameter.detach().cpu().clone()
                for name, parameter in model.named_parameters()
                if parameter.requires_grad
            }

    if best_state is not None:
        state = model.state_dict()
        for name, value in best_state.items():
            state[name].copy_(value.to(device=state[name].device, dtype=state[name].dtype))
        torch.save(best_state, output_dir / "classification_head_state.pt")

    return {
        "global_steps": global_step,
        "optimizer_steps": completed_steps,
        "best_validation_macro_f1": best_macro_f1,
        "history": train_history,
    }


def evaluate_dataset(model, loader, frame, model_name, model_id, train_condition, test_condition, output_dir):
    metrics, labels, predictions = evaluate_model(model, loader)
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
        "num_test_samples": len(loader.dataset),
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
    print(f"MODEL: {model_name} | TRAIN: {train_condition} | METHOD: 4-bit classification-head-only")
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

    train_loader = make_loader(train_ds, tokenizer, TRAIN_BATCH_SIZE, shuffle=True)
    validation_loader = make_loader(validation_ds, tokenizer, EVAL_BATCH_SIZE, shuffle=False)
    model, trainable_head_names = build_model(model_id, tokenizer)

    started = time.time()
    train_metrics = train_head(model, train_loader, validation_loader, output_dir, class_weights)
    tokenizer.save_pretrained(output_dir / "model")
    model.config.save_pretrained(output_dir / "model")

    result_rows = []
    prediction_frames = []
    for test_condition in TEST_DATASETS:
        test_frame = frames[f"{test_condition}_test"].copy()
        test_ds = make_dataset(test_frame, tokenizer)
        test_loader = make_loader(test_ds, tokenizer, EVAL_BATCH_SIZE, shuffle=False)
        result, predictions = evaluate_dataset(
            model, test_loader, test_frame, model_name, model_id, train_condition, test_condition, output_dir
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
            "train_batch_size": TRAIN_BATCH_SIZE,
            "eval_batch_size": EVAL_BATCH_SIZE,
            "gradient_accumulation_steps": GRADIENT_ACCUMULATION_STEPS,
            "effective_batch_size": TRAIN_BATCH_SIZE * GRADIENT_ACCUMULATION_STEPS,
            "max_length": MAX_LENGTH,
            "weight_decay": WEIGHT_DECAY,
            "validation_fraction": VALIDATION_FRACTION,
            "optimizer": OPTIMIZER,
            "fine_tuning_method": "classification_head_only_4bit",
            "trainable_head_names": trainable_head_names,
            "quantization": {
                "load_in_4bit": True,
                "bnb_4bit_quant_type": "nf4",
                "bnb_4bit_use_double_quant": True,
                "bnb_4bit_compute_dtype": str(COMPUTE_DTYPE),
            },
            "lora": None,
            "train_metrics": train_metrics,
        }, handle, indent=2, default=float)

    del model, tokenizer, train_loader, validation_loader, train_ds, validation_ds, full_train
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return results, predictions


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
print(results.round(4).to_string(index=False))
print(matrix.round(4).to_string())
print(f"Finished in {(time.time() - started) / 3600:.2f} hours")
print("Artifacts:", OUTPUT_ROOT.resolve())

try:
    import matplotlib.pyplot as plt
    import seaborn as sns

    plot_matrix = matrix.reindex(columns=TEST_DATASETS)
    plt.figure(figsize=(10, max(3, 0.45 * len(plot_matrix))))
    sns.heatmap(plot_matrix, annot=True, fmt=".4f", cmap="Blues", vmin=0, vmax=1)
    plt.title("4-bit classification-head-only macro-F1")
    plt.xlabel("Test dataset")
    plt.ylabel("Model / training dataset")
    plt.tight_layout()
    plt.savefig(OUTPUT_ROOT / "macro_f1_matrix.png", dpi=180, bbox_inches="tight")
    plt.show()
except ImportError:
    print("matplotlib/seaborn not installed; skipped macro-F1 heatmap.")
