#!/usr/bin/env python3
"""Load a saved 4-bit QLoRA adapter and evaluate it on test datasets.

Run from the repository root, for example:

  python3 templates/qlora_finetuned_model_load.py \
      --model qwen_4b \
      --trained-dataset clean \
      --test-dataset clean,codemix_heavy,transliteration_heavy

The saved layout is:
  benchmark_results/qlora_4bit/<model>/train_<dataset>_seed<seed>/
      adapter/
          adapter_config.json
          adapter_model.safetensors
          tokenizer.json
          tokenizer_config.json
      run_summary.json
      metrics.csv
      predictions.jsonl
"""

from pathlib import Path
import argparse
import dataclasses
import gc
import inspect
import json
import os
import time

import numpy as np
import pandas as pd
import torch
from datasets import ClassLabel, Dataset
from huggingface_hub import get_token, login
from huggingface_hub.errors import GatedRepoError
from peft import PeftModel
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    f1_score,
    precision_recall_fscore_support,
)
from transformers import (
    AutoModelForSequenceClassification,
    AutoTokenizer,
    BitsAndBytesConfig,
    DataCollatorWithPadding,
    Trainer,
    TrainingArguments,
    set_seed,
)


# ============================================================================
# Configuration: edit these defaults or override from the command line.
# ============================================================================
# "clean"  ,"codemix", "transliteration"
SEED = 42
MODEL_NAME = "llama_3b_gated"
TRAINED_DATASET = "transliteration"
TEST_DATASETS = ["compound", "misspell"]

DATA_ROOT = None
ADAPTER_ROOT = Path("benchmark_results/qlora_4bit")
OUTPUT_ROOT = Path("benchmark_results/qlora_4bit_loaded_eval")

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
    "compound_light": {
        "test": Path("outputs/test/compound_light.jsonl"),
    },
    "compound_heavy": {
        "test": Path("outputs/test/compound_heavy.jsonl"),
    },
    "misspell_light": {
        "test": Path("outputs/test/misspell_light.jsonl"),
    },
    "misspell_heavy": {
        "test": Path("outputs/test/misspell_heavy.jsonl"),
    },
}

TRAINABLE_DATASETS = {
    name
    for name, paths in DATASETS.items()
    if "train" in paths
}

DATASET_ALIASES = {
    "codemix": "codemix_heavy",
    "transliteration": "transliteration_heavy",
    "compound": "compound_heavy",
    "misspell": "misspell_heavy",
}

METRICS_COLUMNS = [
    "Model",
    "Trained Noise Condition",
    "Test Noise Condition",
    "Train Size",
    "Test Size",
    "Accuracy",
    "Macro F1",
    "balanced_accuracy",
    "Precision (Offensive)",
    "Recall (Offensive)",
    "F1 (Offensive)",
    "Precision (Not-Offensive)",
    "Recall (Not-Offensive)",
    "F1 (Not-Offensive)",
    "Support (Offensive)",
    "Support (Not-Offensive)",
]

METRICS_RENAME = {
    "model": "Model",
    "train_dataset": "Trained Noise Condition",
    "test_dataset": "Test Noise Condition",
    "train_size": "Train Size",
    "num_test_samples": "Test Size",
    "accuracy": "Accuracy",
    "macro_f1": "Macro F1",
    "balanced_accuracy": "balanced_accuracy",
    "off_precision": "Precision (Offensive)",
    "off_recall": "Recall (Offensive)",
    "off_f1": "F1 (Offensive)",
    "not_precision": "Precision (Not-Offensive)",
    "not_recall": "Recall (Not-Offensive)",
    "not_f1": "F1 (Not-Offensive)",
    "off_support": "Support (Offensive)",
    "not_support": "Support (Not-Offensive)",
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
        description="Load a saved SLM 4-bit QLoRA adapter and evaluate it.",
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
    parser.add_argument("--adapter-root", type=Path, default=ADAPTER_ROOT)
    parser.add_argument("--output-root", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--batch-size", type=int, default=EVAL_BATCH_SIZE)
    parser.add_argument("--max-length", type=int, default=None)
    parser.add_argument("--no-4bit", action="store_true", help="Load the base model without bitsandbytes 4-bit quantization.")
    parser.add_argument("--list-saved", action="store_true", help="Print saved QLoRA adapters and exit.")
    return parser.parse_args()


def run_name_to_dataset(run_name):
    if run_name.startswith("train_") and "_seed" in run_name:
        return run_name[len("train_"):run_name.rfind("_seed")]
    return run_name


def saved_adapter_rows(adapter_root):
    rows = []
    for config_path in sorted(Path(adapter_root).glob("*/*/adapter/adapter_config.json")):
        adapter_dir = config_path.parent
        run_dir = adapter_dir.parent
        model_name = run_dir.parent.name
        summary_path = run_dir / "run_summary.json"
        summary = {}
        if summary_path.is_file():
            with summary_path.open(encoding="utf-8") as handle:
                summary = json.load(handle)
        with config_path.open(encoding="utf-8") as handle:
            adapter_config = json.load(handle)
        rows.append({
            "model": model_name,
            "trained_dataset": summary.get("train_condition", run_name_to_dataset(run_dir.name)),
            "seed": summary.get("seed", "?"),
            "model_id": summary.get("model_id", adapter_config.get("base_model_name_or_path", MODELS.get(model_name, "?"))),
            "adapter": str(adapter_dir),
        })
    return rows


def print_saved_adapters(adapter_root):
    rows = saved_adapter_rows(adapter_root)
    if not rows:
        print(f"No saved QLoRA adapters found below {Path(adapter_root).resolve()}")
        return
    print("Saved QLoRA adapters:")
    print(pd.DataFrame(rows).to_string(index=False))


def artifact_dir(adapter_root, model_name, trained_dataset, seed):
    return Path(adapter_root) / model_name / f"train_{trained_dataset}_seed{seed}"


def load_json(path):
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def load_run_summary(run_dir):
    path = run_dir / "run_summary.json"
    return load_json(path) if path.is_file() else {}


def load_adapter_config(adapter_dir):
    path = Path(adapter_dir) / "adapter_config.json"
    if not path.is_file():
        raise FileNotFoundError(f"Missing PEFT adapter config: {path}")
    return load_json(path)


def validate_selection(args):
    trained_dataset = normalize_dataset_name(args.trained_dataset)
    test_datasets = [normalize_dataset_name(name) for name in (split_csv(args.test_dataset) if args.test_dataset else TEST_DATASETS)]

    unknown = set(test_datasets) - set(DATASETS)
    if unknown:
        raise KeyError(f"Undefined test dataset names: {sorted(unknown)}")
    if trained_dataset not in TRAINABLE_DATASETS:
        raise ValueError(
            f"{trained_dataset!r} is not available for --trained-dataset. "
            f"Trainable adapter datasets are: {sorted(TRAINABLE_DATASETS)}"
        )

    run_dir = artifact_dir(args.adapter_root, args.model, trained_dataset, args.seed)
    adapter_dir = run_dir / "adapter"
    config_path = adapter_dir / "adapter_config.json"
    model_path = adapter_dir / "adapter_model.safetensors"
    if not config_path.is_file() or not model_path.is_file():
        print_saved_adapters(args.adapter_root)
        raise FileNotFoundError(f"Missing adapter files below: {adapter_dir}")

    return trained_dataset, test_datasets, run_dir, adapter_dir


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


def count_jsonl_rows(path):
    with Path(path).open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def format_metrics_for_csv(results):
    return results.rename(columns=METRICS_RENAME).reindex(columns=METRICS_COLUMNS)


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


def from_pretrained_dtype_kwargs(dtype):
    parameters = inspect.signature(AutoModelForSequenceClassification.from_pretrained).parameters
    if "dtype" in parameters:
        return {"dtype": dtype}
    return {"torch_dtype": dtype}


def build_tokenizer(adapter_dir, model_id, hf_kwargs):
    tokenizer_source = adapter_dir if (Path(adapter_dir) / "tokenizer_config.json").is_file() else model_id
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            tokenizer_source,
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
    print("Tokenizer:", tokenizer_source)
    return tokenizer


def build_base_model(model_id, tokenizer, load_in_4bit, dtype, hf_kwargs):
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
            "attn_implementation": "sdpa",
            **from_pretrained_dtype_kwargs(dtype),
        })
    else:
        if torch.cuda.is_available():
            model_kwargs.update({"device_map": "auto", **from_pretrained_dtype_kwargs(dtype)})
        else:
            model_kwargs.update(from_pretrained_dtype_kwargs(torch.float32))

    try:
        model = AutoModelForSequenceClassification.from_pretrained(model_id, **model_kwargs)
    except (GatedRepoError, OSError) as exc:
        if "gated repo" in str(exc).lower() or "restricted" in str(exc).lower():
            explain_gated_model_error(model_id, exc)
        raise

    if model.config.pad_token_id is None:
        model.config.pad_token_id = tokenizer.pad_token_id
    model.config.use_cache = False
    return model


def load_qlora_model(model_id, adapter_dir, tokenizer, load_in_4bit, dtype, hf_kwargs):
    base_model = build_base_model(model_id, tokenizer, load_in_4bit, dtype, hf_kwargs)
    peft_kwargs = {"is_trainable": False}
    if "token" in inspect.signature(PeftModel.from_pretrained).parameters and "token" in hf_kwargs:
        peft_kwargs["token"] = hf_kwargs["token"]
    model = PeftModel.from_pretrained(base_model, adapter_dir, **peft_kwargs)
    model.eval()
    print("Loaded QLoRA adapter:", adapter_dir)
    return model


def make_dataset(frame, tokenizer, max_length):
    dataset = Dataset.from_pandas(frame[["id", "text", "label"]], preserve_index=False)
    dataset = dataset.cast_column("label", ClassLabel(names=["NOT", "OFF"]))
    return dataset.map(
        lambda batch: tokenizer(batch["text"], truncation=True, max_length=max_length),
        batched=True,
        remove_columns=["text"],
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


def prediction_arguments(output_dir, seed, batch_size, dtype):
    kwargs = {
        "output_dir": str(output_dir / "trainer_tmp"),
        "seed": seed,
        "per_device_eval_batch_size": batch_size,
        "eval_accumulation_steps": 8,
        "fp16": dtype == torch.float16,
        "bf16": dtype == torch.bfloat16,
        "report_to": "none",
        "dataloader_num_workers": 2,
        "dataloader_pin_memory": False,
        "label_names": ["labels"],
    }
    valid = {field.name for field in dataclasses.fields(TrainingArguments)}
    return TrainingArguments(**{key: value for key, value in kwargs.items() if key in valid})


def evaluate_dataset(trainer, dataset, frame, test_dataset, config, output_dir):
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
        "model": config["model_name"],
        "model_id": config["model_id"],
        "train_dataset": config["trained_dataset"],
        "test_dataset": test_dataset,
        "train_size": config["train_size"],
        "num_test_samples": len(dataset),
        "off_support": int(np.sum(labels == 1)),
        "not_support": int(np.sum(labels == 0)),
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
        print_saved_adapters(args.adapter_root)
        return

    trained_dataset, test_datasets, run_dir, adapter_dir = validate_selection(args)
    summary = load_run_summary(run_dir)
    adapter_config = load_adapter_config(adapter_dir)
    max_length = args.max_length or int(summary.get("max_length", MAX_LENGTH))
    model_id = adapter_config.get("base_model_name_or_path") or summary.get("model_id") or MODELS[args.model]
    load_in_4bit = LOAD_IN_4BIT and not args.no_4bit

    print_saved_adapters(args.adapter_root)
    print()
    print("=" * 80)
    print(f"MODEL: {args.model} ({model_id})")
    print(f"TRAINED DATASET: {trained_dataset}")
    print(f"TEST DATASETS: {test_datasets}")
    print(f"ADAPTER: {adapter_dir}")
    print("=" * 80)

    set_seed(args.seed)
    np.random.seed(args.seed)

    data_root = find_data_root(args.data_root, test_datasets)
    print("DATA_ROOT =", data_root.resolve())
    frames = load_test_frames(data_root, test_datasets)
    train_size = count_jsonl_rows(Path(data_root) / DATASETS[trained_dataset]["train"])
    print(f"TRAIN SIZE: {train_size}")

    dtype = compute_dtype()
    print("torch", torch.__version__, "| CUDA", torch.cuda.is_available(), "| dtype", dtype)
    hf_kwargs = auth_kwargs()

    started = time.time()
    tokenizer = build_tokenizer(adapter_dir, model_id, hf_kwargs)
    model = load_qlora_model(model_id, adapter_dir, tokenizer, load_in_4bit, dtype, hf_kwargs)

    output_dir = Path(args.output_root) / args.model / f"train_{trained_dataset}_seed{args.seed}"
    output_dir.mkdir(parents=True, exist_ok=True)

    trainer = Trainer(
        model=model,
        args=prediction_arguments(output_dir, args.seed, args.batch_size, dtype),
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer, pad_to_multiple_of=8),
        compute_metrics=compute_metrics,
        **trainer_tokenizer_kwargs(tokenizer),
    )

    config = {
        "model_name": args.model,
        "model_id": model_id,
        "trained_dataset": trained_dataset,
        "test_datasets": test_datasets,
        "train_size": train_size,
        "seed": args.seed,
        "max_length": max_length,
        "batch_size": args.batch_size,
        "load_in_4bit": load_in_4bit,
        "source_run_dir": str(run_dir),
        "source_adapter_dir": str(adapter_dir),
        "adapter_config": adapter_config,
    }

    result_rows = []
    prediction_frames = []
    for test_dataset in test_datasets:
        test_dataset_hf = make_dataset(frames[test_dataset], tokenizer, max_length)
        result, predictions = evaluate_dataset(trainer, test_dataset_hf, frames[test_dataset], test_dataset, config, output_dir)
        result["elapsed_hours"] = (time.time() - started) / 3600
        result_rows.append(result)
        prediction_frames.append(predictions)
        print(f"{test_dataset:24s} macro_f1={result['macro_f1']:.4f} accuracy={result['accuracy']:.4f}")

    results = pd.DataFrame(result_rows)
    metrics_for_csv = format_metrics_for_csv(results)
    predictions = pd.concat(prediction_frames, ignore_index=True)
    metrics_for_csv.to_csv(output_dir / "metrics.csv", index=False)
    predictions.to_json(output_dir / "predictions.jsonl", orient="records", lines=True, force_ascii=False)

    with (output_dir / "run_summary.json").open("w", encoding="utf-8") as handle:
        json.dump({
            **config,
            "output_dir": str(output_dir),
            "elapsed_hours": (time.time() - started) / 3600,
        }, handle, indent=2)

    print()
    print(metrics_for_csv.round(4).to_string(index=False))
    print("Artifacts:", output_dir.resolve())

    del trainer, model, tokenizer
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


if __name__ == "__main__":
    main()
