#!/usr/bin/env python3
"""Load a saved 4-bit classification head and evaluate it on a test dataset.

Run from the repository root, for example:

  python3 templates/classificationhead_load.py \
      --model llama_3b_gated \
      --trained-dataset clean \
      --test-dataset codemix_heavy

The saved layout is:
  benchmark_results/classification_head_4bit/<model>/train_<dataset>_seed<seed>/
      classification_head_state.pt
      run_summary.json
      metrics.csv
      predictions.jsonl
"""

from pathlib import Path
import argparse
import gc
import json
import os
import time

import numpy as np
import pandas as pd
import torch
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
    set_seed,
)


# ============================================================================
# Configuration: edit these defaults or override from the command line.
# ============================================================================

SEED = 42
MODEL_NAME = "llama_3b_gated"
TRAINED_DATASET = "clean"
TEST_DATASETS = ["clean"]

DATA_ROOT = None
HEAD_ROOT = Path("benchmark_results/classification_head_4bit")
OUTPUT_ROOT = Path("benchmark_results/classification_head_4bit_loaded_eval")

NUM_LABELS = 2
LABEL_NAME = {0: "NOT", 1: "OFF"}
LABEL2ID = {value: key for key, value in LABEL_NAME.items()}

MAX_LENGTH = 128
EVAL_BATCH_SIZE = 8
LOAD_IN_4BIT = True

MODELS = {
    "qwen_4b": "Qwen/Qwen3-4B",
    "qwen_8b": "Qwen/Qwen3-8B",
    "llama_3b_gated": "meta-llama/Llama-3.2-3B",
    "llama_8b_gated": "meta-llama/Llama-3.1-8B",
    "sinllama_gated": "polyglots/SinLlama_v01",
}

DATASETS = {
    "clean": {
        "train": Path("sold/train.jsonl"),
        "test": Path("sold/test.jsonl"),
    },
    "codemix_light": {
        "train": Path("outputs/train/codemix_light.jsonl"),
        "test": Path("outputs/test/codemix_light.jsonl"),
    },
    "codemix_heavy": {
        "train": Path("outputs/train/codemix_heavy.jsonl"),
        "test": Path("outputs/test/codemix_heavy.jsonl"),
    },
    "transliteration_light": {
        "train": Path("outputs/train/transliteration_light.jsonl"),
        "test": Path("outputs/test/transliteration_light.jsonl"),
    },
    "transliteration_heavy": {
        "train": Path("outputs/train/transliteration_heavy.jsonl"),
        "test": Path("outputs/test/transliteration_heavy.jsonl"),
    },
}

DATASET_ALIASES = {
    "codemix": "codemix_heavy",
    "transliteration": "transliteration_heavy",
}


def split_csv(values):
    names = []
    for value in values:
        names.extend(part.strip() for part in value.split(",") if part.strip())
    return names


def normalize_dataset_name(name):
    return DATASET_ALIASES.get(name, name)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Load a saved SLM 4-bit classification head and evaluate it.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--model", default=MODEL_NAME, choices=sorted(MODELS))
    parser.add_argument("--trained-dataset", default=TRAINED_DATASET)
    parser.add_argument(
        "--test-dataset",
        action="append",
        default=None,
        help="Test dataset name. Repeat or pass comma-separated values.",
    )
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--head-root", type=Path, default=HEAD_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--batch-size", type=int, default=EVAL_BATCH_SIZE)
    parser.add_argument("--max-length", type=int, default=None)
    parser.add_argument("--no-4bit", action="store_true", help="Load the base model without bitsandbytes 4-bit quantization.")
    parser.add_argument("--list-saved", action="store_true", help="Print saved head artifacts and exit.")
    return parser.parse_args()


def saved_head_rows(head_root):
    rows = []
    for state_path in sorted(Path(head_root).glob("*/*/classification_head_state.pt")):
        run_dir = state_path.parent
        model_name = run_dir.parent.name
        trained_dataset = run_dir.name
        if trained_dataset.startswith("train_") and "_seed" in trained_dataset:
            trained_dataset = trained_dataset[len("train_"):trained_dataset.rfind("_seed")]
        summary_path = run_dir / "run_summary.json"
        summary = {}
        if summary_path.is_file():
            with summary_path.open(encoding="utf-8") as handle:
                summary = json.load(handle)
        rows.append({
            "model": model_name,
            "trained_dataset": trained_dataset,
            "seed": summary.get("seed", "?"),
            "model_id": summary.get("model_id", MODELS.get(model_name, "?")),
            "path": str(run_dir),
        })
    return rows


def print_saved_heads(head_root):
    rows = saved_head_rows(head_root)
    if not rows:
        print(f"No saved heads found below {Path(head_root).resolve()}")
        return
    print("Saved classification heads:")
    print(pd.DataFrame(rows).to_string(index=False))


def artifact_dir(head_root, model_name, trained_dataset, seed):
    return Path(head_root) / model_name / f"train_{trained_dataset}_seed{seed}"


def load_run_summary(run_dir):
    path = run_dir / "run_summary.json"
    if not path.is_file():
        return {}
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_selection(args):
    trained_dataset = normalize_dataset_name(args.trained_dataset)
    test_datasets = [normalize_dataset_name(name) for name in (split_csv(args.test_dataset) if args.test_dataset else TEST_DATASETS)]

    unknown = {trained_dataset, *test_datasets} - set(DATASETS)
    if unknown:
        raise KeyError(f"Undefined dataset names: {sorted(unknown)}")

    run_dir = artifact_dir(args.head_root, args.model, trained_dataset, args.seed)
    state_path = run_dir / "classification_head_state.pt"
    if not state_path.is_file():
        print_saved_heads(args.head_root)
        raise FileNotFoundError(f"Missing saved head: {state_path}")

    return trained_dataset, test_datasets, run_dir, state_path


def required_data_paths(test_datasets):
    return [DATASETS[name]["test"] for name in test_datasets]


def is_data_root(path, test_datasets):
    path = Path(path)
    return all((path / rel).is_file() for rel in required_data_paths(test_datasets))


def find_data_root(explicit, test_datasets):
    if explicit is not None:
        explicit = Path(explicit)
        if not is_data_root(explicit, test_datasets):
            raise FileNotFoundError(f"Selected test files were not found below DATA_ROOT: {explicit.resolve()}")
        return explicit

    cwd = Path.cwd().resolve()
    for parent in (cwd, *cwd.parents):
        for candidate in (parent / "data", parent):
            if is_data_root(candidate, test_datasets):
                return candidate

    kaggle = Path("/kaggle/input")
    if kaggle.exists():
        for candidate in kaggle.iterdir():
            if candidate.is_dir() and is_data_root(candidate, test_datasets):
                return candidate

    raise FileNotFoundError("Could not locate selected test files. Set DATA_ROOT explicitly.")


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
        "0": 0,
        "1": 1,
        "NOT": 0,
        "OFF": 1,
        "not": 0,
        "off": 1,
        "negative": 0,
        "positive": 1,
        "not-offensive": 0,
        "offensive": 1,
        "non-hate": 0,
        "hate": 1,
    }
    normalized = labels.astype(str).str.strip().map(mapping)
    if normalized.isna().any():
        bad = sorted(labels[normalized.isna()].astype(str).unique().tolist())
        raise ValueError(f"Unmapped labels: {bad}")
    return normalized.astype(int)


def canonicalize(df, condition, split):
    id_candidates = ("post_id", "source_id", "id", "sentence_id", "orig_id")
    text_candidates = ("text", "noisy_text", "transliterated", "transliteration", "romanized")
    id_col = next((column for column in id_candidates if column in df.columns), None)
    text_col = next((column for column in text_candidates if column in df.columns), None)
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


def load_test_frames(data_root, test_datasets):
    frames = {}
    for name in test_datasets:
        path = Path(data_root) / DATASETS[name]["test"]
        frame = canonicalize(read_jsonl(path), name, "test")
        frames[name] = frame
        counts = frame["label"].value_counts().sort_index().to_dict()
        print(f"{name + '_test':32s} n={len(frame):5d} labels={counts} path={path}")
    return frames


def compute_dtype():
    if torch.cuda.is_available() and torch.cuda.is_bf16_supported():
        return torch.bfloat16
    if torch.cuda.is_available():
        return torch.float16
    return torch.float32


def auth_kwargs():
    token = os.environ.get("HF_TOKEN") or get_token()
    if os.environ.get("HF_TOKEN"):
        login(token=token, add_to_git_credential=False)
        print("Authenticated from HF_TOKEN.")
    elif token:
        print("Using Hugging Face token cache.")
    else:
        print("HF_TOKEN is not set. Ungated models will work; gated models need approved access.")
    return {"token": token} if token else {}


def explain_gated_model_error(model_id, exc):
    raise RuntimeError(
        f"Cannot access gated Hugging Face model '{model_id}'. "
        "Request access on the model page and set HF_TOKEN to an approved token."
    ) from exc


def build_tokenizer(model_id, hf_kwargs):
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=True,
            use_fast=True,
            **hf_kwargs,
        )
    except (GatedRepoError, OSError) as exc:
        if "gated repo" in str(exc).lower() or "restricted" in str(exc).lower():
            explain_gated_model_error(model_id, exc)
        raise

    tokenizer.padding_side = "right"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    return tokenizer


def build_model(model_id, tokenizer, load_in_4bit, dtype, hf_kwargs):
    model_kwargs = {
        "num_labels": NUM_LABELS,
        "id2label": LABEL_NAME,
        "label2id": LABEL2ID,
        "pad_token_id": tokenizer.pad_token_id,
        "trust_remote_code": True,
        "low_cpu_mem_usage": True,
        **hf_kwargs,
    }

    if load_in_4bit:
        if not torch.cuda.is_available():
            raise RuntimeError("4-bit loading requires CUDA and bitsandbytes. Use --no-4bit for a full precision CPU/GPU load.")
        model_kwargs.update({
            "quantization_config": BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_quant_type="nf4",
                bnb_4bit_use_double_quant=True,
                bnb_4bit_compute_dtype=dtype,
            ),
            "device_map": "auto",
            "torch_dtype": dtype,
            "attn_implementation": "sdpa",
        })
    else:
        if torch.cuda.is_available():
            model_kwargs.update({"device_map": "auto", "torch_dtype": dtype})
        else:
            model_kwargs.update({"torch_dtype": torch.float32})

    try:
        model = AutoModelForSequenceClassification.from_pretrained(model_id, **model_kwargs)
    except (GatedRepoError, OSError) as exc:
        if "gated repo" in str(exc).lower() or "restricted" in str(exc).lower():
            explain_gated_model_error(model_id, exc)
        raise

    if model.config.pad_token_id is None:
        model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False
    for parameter in model.parameters():
        parameter.requires_grad = False
    return model


def torch_load_cpu(path):
    try:
        return torch.load(path, map_location="cpu", weights_only=True)
    except TypeError:
        return torch.load(path, map_location="cpu")


def load_classification_head(model, state_path):
    saved_state = torch_load_cpu(state_path)
    if not isinstance(saved_state, dict):
        raise TypeError(f"Expected a state dict in {state_path}, got {type(saved_state)!r}")

    model_state = model.state_dict()
    missing = [name for name in saved_state if name not in model_state]
    mismatched = [
        (name, tuple(value.shape), tuple(model_state[name].shape))
        for name, value in saved_state.items()
        if name in model_state and tuple(value.shape) != tuple(model_state[name].shape)
    ]
    if missing or mismatched:
        if missing:
            print("Missing keys in rebuilt model:", missing)
        if mismatched:
            print("Shape mismatches:", mismatched)
        raise RuntimeError("Saved classification head does not match the rebuilt model.")

    with torch.no_grad():
        for name, value in saved_state.items():
            target = model_state[name]
            target.copy_(value.to(device=target.device, dtype=target.dtype))

    print("Loaded classification head tensors:")
    for name, value in saved_state.items():
        print(f"  {name:48s} shape={tuple(value.shape)} dtype={value.dtype}")


def make_dataset(frame, tokenizer, max_length):
    dataset = Dataset.from_pandas(frame[["id", "text", "label"]], preserve_index=False)
    dataset = dataset.cast_column("label", ClassLabel(names=["NOT", "OFF"]))
    return dataset.map(
        lambda batch: tokenizer(batch["text"], truncation=True, max_length=max_length),
        batched=True,
        remove_columns=["text"],
    )


def make_loader(dataset, tokenizer, batch_size):
    dataset = dataset.remove_columns([name for name in ("id",) if name in dataset.column_names])
    dataset = dataset.rename_column("label", "labels")
    dataset.set_format(type="torch")
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        collate_fn=DataCollatorWithPadding(tokenizer=tokenizer, pad_to_multiple_of=8),
        num_workers=2,
        pin_memory=False,
    )


def metric_values(labels, predictions):
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels,
        predictions,
        labels=[0, 1],
        zero_division=0,
    )
    return {
        "accuracy": accuracy_score(labels, predictions),
        "balanced_accuracy": balanced_accuracy_score(labels, predictions),
        "macro_f1": f1_score(labels, predictions, average="macro", zero_division=0),
        "not_precision": precision[0],
        "not_recall": recall[0],
        "not_f1": f1[0],
        "off_precision": precision[1],
        "off_recall": recall[1],
        "off_f1": f1[1],
    }


def model_device(model):
    return next(model.parameters()).device


def evaluate_model(model, loader):
    model.eval()
    labels_out = []
    predictions_out = []
    device = model_device(model)

    with torch.no_grad():
        for batch in tqdm(loader, desc="predict", leave=False):
            labels = batch.pop("labels").to(device)
            batch = {key: value.to(device) for key, value in batch.items()}
            outputs = model(**batch)
            predictions = torch.argmax(outputs.logits, dim=-1)
            labels_out.append(labels.detach().cpu().numpy())
            predictions_out.append(predictions.detach().cpu().numpy())

    labels = np.concatenate(labels_out)
    predictions = np.concatenate(predictions_out)
    return metric_values(labels, predictions), labels, predictions


def evaluate_dataset(model, tokenizer, frame, test_dataset, config, output_dir):
    dataset = make_dataset(frame, tokenizer, config["max_length"])
    loader = make_loader(dataset, tokenizer, config["batch_size"])
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
        "model": config["model_name"],
        "model_id": config["model_id"],
        "train_dataset": config["trained_dataset"],
        "test_dataset": test_dataset,
        "num_test_samples": len(frame),
        **metrics,
    }
    predictions_frame = pd.DataFrame({
        "id": frame["id"].to_numpy(),
        "model": config["model_name"],
        "train_dataset": config["trained_dataset"],
        "test_dataset": test_dataset,
        "label": labels,
        "prediction": predictions,
        "label_name": [LABEL_NAME[int(label)] for label in labels],
        "prediction_name": [LABEL_NAME[int(prediction)] for prediction in predictions],
        "text": frame["text"].to_numpy(),
    })

    with (output_dir / f"{test_dataset}_classification_report.json").open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
    return result, predictions_frame


def main():
    args = parse_args()
    if args.list_saved:
        print_saved_heads(args.head_root)
        return

    trained_dataset, test_datasets, run_dir, state_path = validate_selection(args)
    summary = load_run_summary(run_dir)
    max_length = args.max_length or int(summary.get("max_length", MAX_LENGTH))
    model_id = summary.get("model_id", MODELS[args.model])
    load_in_4bit = LOAD_IN_4BIT and not args.no_4bit

    print_saved_heads(args.head_root)
    print()
    print("=" * 80)
    print(f"MODEL: {args.model} ({model_id})")
    print(f"TRAINED DATASET: {trained_dataset}")
    print(f"TEST DATASETS: {test_datasets}")
    print(f"SAVED HEAD: {state_path}")
    print("=" * 80)

    set_seed(args.seed)
    np.random.seed(args.seed)

    data_root = find_data_root(args.data_root, test_datasets)
    print("DATA_ROOT =", data_root.resolve())
    frames = load_test_frames(data_root, test_datasets)

    dtype = compute_dtype()
    print("torch", torch.__version__, "| CUDA", torch.cuda.is_available(), "| dtype", dtype)
    hf_kwargs = auth_kwargs()

    started = time.time()
    tokenizer = build_tokenizer(model_id, hf_kwargs)
    model = build_model(model_id, tokenizer, load_in_4bit, dtype, hf_kwargs)
    load_classification_head(model, state_path)

    output_dir = Path(args.output_root) / args.model / f"train_{trained_dataset}_seed{args.seed}"
    output_dir.mkdir(parents=True, exist_ok=True)

    config = {
        "model_name": args.model,
        "model_id": model_id,
        "trained_dataset": trained_dataset,
        "test_datasets": test_datasets,
        "seed": args.seed,
        "max_length": max_length,
        "batch_size": args.batch_size,
        "load_in_4bit": load_in_4bit,
        "source_head_dir": str(run_dir),
        "source_head_state": str(state_path),
    }

    result_rows = []
    prediction_frames = []
    for test_dataset in test_datasets:
        result, predictions = evaluate_dataset(model, tokenizer, frames[test_dataset], test_dataset, config, output_dir)
        result["elapsed_hours"] = (time.time() - started) / 3600
        result_rows.append(result)
        prediction_frames.append(predictions)
        print(f"{test_dataset:24s} macro_f1={result['macro_f1']:.4f} accuracy={result['accuracy']:.4f}")

    results = pd.DataFrame(result_rows)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    results.to_csv(output_dir / "metrics.csv", index=False)
    predictions.to_json(output_dir / "predictions.jsonl", orient="records", lines=True, force_ascii=False)

    with (output_dir / "run_summary.json").open("w", encoding="utf-8") as handle:
        json.dump({
            **config,
            "output_dir": str(output_dir),
            "elapsed_hours": (time.time() - started) / 3600,
        }, handle, indent=2)

    print()
    print(results.round(4).to_string(index=False))
    print("Artifacts:", output_dir.resolve())

    del model, tokenizer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
