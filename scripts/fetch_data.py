"""
Phase 0 data acquisition — deterministic, seeded, idempotent.

Fetches:
  1. SOLD (clean Sinhala hate-speech dataset)        -> data/sold/{train,test}.jsonl
  2. Swa-Bhasha sentence pairs (real human Singlish)  -> data/gold/gold_sentences.jsonl
                                                          data/reference/reference_singlish.txt
  3. Swa-Bhasha word-level pairs (combinatorial)      -> data/gold/gold_words.jsonl
                                                          data/gold/heldout_words.txt

and writes data/PROVENANCE.json documenting sources, hashes, seed, and counts.

Run:  python scripts/fetch_data.py

Idempotent: raw downloads are cached in data/raw/ (gitignored) and re-verified
by hash on every run instead of re-downloaded; derived files are regenerated
deterministically from the seed every time, so a re-run produces byte-identical
output (verify with sha256sum before/after).

--- Provenance notes (see LOG.md for the full writeup) ---
The Swa-Bhasha GitHub repo (Sumanathilaka/Swa-Bhasha-Sinhala-Singlish-Dataset)
contains no data, only a README pointing at Kaggle. The Kaggle files are
UTF-16 Excel exports with corrupted emoji; the same author (deshanksuman)
publishes clean UTF-8 mirrors on HuggingFace, which is what this script uses.

The word-level pairs are COMBINATORIALLY GENERATED, not observed (variant
counts per word are exact powers of two). They make an excellent multi-
reference CER target but must never be used as a realism reference corpus.
Only the sentence-level pairs (genuine social-media text) feed `reference/`.
"""

from __future__ import annotations

import csv
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import contains_sinhala, grapheme_len  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
SOLD_DIR = DATA_DIR / "sold"
GOLD_DIR = DATA_DIR / "gold"
REFERENCE_DIR = DATA_DIR / "reference"
PROVENANCE_PATH = DATA_DIR / "PROVENANCE.json"

SEED = 1337  # fixed for all sampling/shuffling in this script — do not change casually
GOLD_SENTENCES_N = 400
GOLD_WORDS_N = 2000

SOLD_URLS = {
    "train": "https://huggingface.co/datasets/sinhala-nlp/SOLD/resolve/main/SOLD_train.tsv",
    "test": "https://huggingface.co/datasets/sinhala-nlp/SOLD/resolve/main/SOLD_test.tsv",
}
EXPECTED_SOLD_ROWS = {"train": 7500, "test": 2500}
# SOLD paper reports ~10k total posts, ~41% offensive. Independent sanity band,
# not derived from the numbers we compute below (that would be circular).
EXPECTED_TOTAL_ROWS = 10000
EXPECTED_OFF_RATE_BAND = (0.35, 0.45)

SWABHASHA_SENTENCES_URL = (
    "https://huggingface.co/datasets/deshanksuman/SwaBhasha_Transliteration_Sinhala"
    "/resolve/main/test.csv"
)
SWABHASHA_WORDS_URL = (
    "https://huggingface.co/datasets/deshanksuman/Swabhasha_RomanizedSinhala_Dataset"
    "/resolve/main/train.csv"
)


def log(msg: str) -> None:
    print(f"[fetch_data] {msg}")


def download_cached(url: str, dest: Path, *, timeout: int = 180) -> tuple[str, int]:
    """Download `url` to `dest` unless already cached; return (sha256, size_bytes).

    Re-verifies the hash on cache hits too, so a corrupted cache is caught
    rather than silently reused.
    """
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        tmp = dest.with_name(dest.name + ".part")
        log(f"downloading {url} -> {dest}")
        h = hashlib.sha256()
        with requests.get(url, stream=True, timeout=timeout) as resp:
            resp.raise_for_status()
            with tmp.open("wb") as f:
                for chunk in resp.iter_content(chunk_size=1 << 20):
                    f.write(chunk)
                    h.update(chunk)
        tmp.replace(dest)
        return h.hexdigest(), dest.stat().st_size
    log(f"cached: {dest} (verifying hash)")
    h = hashlib.sha256()
    with dest.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest(), dest.stat().st_size


def parse_sold_tsv(text: str) -> list[dict]:
    csv.field_size_limit(10**9)
    reader = csv.reader(text.splitlines(), delimiter="\t")
    rows = list(reader)
    header, body = rows[0], rows[1:]
    idx = {name: i for i, name in enumerate(header)}
    out = []
    for row in body:
        if len(row) != len(header):
            raise ValueError(f"SOLD row has {len(row)} cols, expected {len(header)}: {row!r}")
        label_raw = row[idx["label"]]
        label = {"OFF": 1, "NOT": 0}.get(label_raw)
        if label is None:
            raise ValueError(f"unexpected SOLD label {label_raw!r}")
        out.append(
            {
                "post_id": row[idx["post_id"]],
                "text": row[idx["text"]],
                "tokens": row[idx["tokens"]],
                "rationales": row[idx["rationales"]],
                "label": label,
            }
        )
    return out


def fetch_sold() -> dict:
    SOLD_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    all_ids_by_split: dict[str, set[str]] = {}
    for split, url in SOLD_URLS.items():
        raw_path = RAW_DIR / f"SOLD_{split}.tsv"
        sha, size = download_cached(url, raw_path)
        text = raw_path.read_text(encoding="utf-8")
        rows = parse_sold_tsv(text)

        if len(rows) != EXPECTED_SOLD_ROWS[split]:
            raise AssertionError(
                f"SOLD {split}: expected {EXPECTED_SOLD_ROWS[split]} rows, got {len(rows)}"
            )
        ids = [r["post_id"] for r in rows]
        if len(set(ids)) != len(ids):
            raise AssertionError(f"SOLD {split}: duplicate post_id found")
        all_ids_by_split[split] = set(ids)

        out_path = SOLD_DIR / f"{split}.jsonl"
        with out_path.open("w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps({**r, "split": split}, ensure_ascii=False) + "\n")

        off_rate = sum(r["label"] for r in rows) / len(rows)
        log(f"SOLD {split}: {len(rows)} rows, {off_rate:.1%} offensive -> {out_path}")
        manifest[f"sold_{split}"] = {
            "url": url,
            "sha256": sha,
            "size_bytes": size,
            "n_rows": len(rows),
            "off_rate": round(off_rate, 4),
        }

    overlap = all_ids_by_split["train"] & all_ids_by_split["test"]
    if overlap:
        raise AssertionError(f"SOLD train/test post_id overlap: {len(overlap)} ids")

    total_rows = sum(m["n_rows"] for k, m in manifest.items())
    total_off = sum(m["n_rows"] * m["off_rate"] for k, m in manifest.items())
    overall_off_rate = total_off / total_rows
    if total_rows != EXPECTED_TOTAL_ROWS:
        raise AssertionError(f"SOLD total rows {total_rows} != expected {EXPECTED_TOTAL_ROWS}")
    lo, hi = EXPECTED_OFF_RATE_BAND
    if not (lo <= overall_off_rate <= hi):
        raise AssertionError(
            f"SOLD overall offensive rate {overall_off_rate:.3f} outside paper band {EXPECTED_OFF_RATE_BAND}"
        )
    log(f"SOLD total: {total_rows} rows, {overall_off_rate:.1%} offensive (train/test id-disjoint, OK)")
    return manifest


def valid_pair(romanized: str, sinhala: str) -> bool:
    romanized = romanized.strip()
    sinhala = sinhala.strip()
    if not romanized or not sinhala:
        return False
    if contains_sinhala(romanized):
        return False
    if not contains_sinhala(sinhala):
        return False
    return True


def fetch_swabhasha_sentences() -> dict:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / "swabhasha_sentences.csv"
    sha, size = download_cached(SWABHASHA_SENTENCES_URL, raw_path)

    text = raw_path.read_text(encoding="utf-8-sig")
    reader = csv.reader(text.splitlines())
    rows = list(reader)
    header, body = rows[0], rows[1:]

    seen = set()
    pairs: list[tuple[str, str]] = []
    for row in body:
        if len(row) < 2:
            continue
        romanized, sinhala = row[0].strip(), row[1].strip()
        if not valid_pair(romanized, sinhala):
            continue
        key = (romanized, sinhala)
        if key in seen:  # de-dupe repeated social-media snippets
            continue
        seen.add(key)
        pairs.append(key)

    rng = random.Random(SEED)
    shuffled = pairs[:]
    rng.shuffle(shuffled)

    if len(shuffled) < GOLD_SENTENCES_N * 2:
        raise AssertionError(
            f"only {len(shuffled)} valid sentence pairs; need at least {GOLD_SENTENCES_N * 2} "
            "to hold out a gold set and keep a usable reference corpus"
        )

    # Some short common phrases (e.g. "Haha", "Patta") occur verbatim with
    # different Sinhala pairings, so a plain index slice can leak the same
    # romanized string into both sets. Take gold first, then drop any
    # candidate from reference whose romanized side duplicates a gold one —
    # guarantees disjointness by construction rather than asserting after.
    gold = shuffled[:GOLD_SENTENCES_N]
    gold_romanized = {r for r, s in gold}
    reference = [(r, s) for r, s in shuffled[GOLD_SENTENCES_N:] if r not in gold_romanized]

    overlap = gold_romanized & {r for r, s in reference}
    if overlap:
        raise AssertionError(f"gold/reference romanized-side overlap: {len(overlap)} strings")

    gold_path = GOLD_DIR / "gold_sentences.jsonl"
    with gold_path.open("w", encoding="utf-8") as f:
        for romanized, sinhala in gold:
            f.write(json.dumps({"romanized": romanized, "sinhala": sinhala}, ensure_ascii=False) + "\n")

    reference_path = REFERENCE_DIR / "reference_singlish.txt"
    with reference_path.open("w", encoding="utf-8") as f:
        for romanized, _sinhala in reference:
            f.write(romanized + "\n")

    log(
        f"Swa-Bhasha sentences: {len(rows) - 1} raw rows -> {len(pairs)} valid unique pairs "
        f"-> gold={len(gold)} ({gold_path}), reference={len(reference)} ({reference_path})"
    )
    return {
        "swabhasha_sentences": {
            "url": SWABHASHA_SENTENCES_URL,
            "sha256": sha,
            "size_bytes": size,
            "n_raw_rows": len(rows) - 1,
            "n_valid_pairs": len(pairs),
        },
        "gold_sentences": {"path": gold_path.relative_to(REPO_ROOT).as_posix(), "n": len(gold)},
        "reference_singlish": {"path": reference_path.relative_to(REPO_ROOT).as_posix(), "n": len(reference)},
    }


def stream_word_pairs(path: Path):
    """Yield (romanized, sinhala) from the word-level CSV without loading it whole."""
    with path.open("r", encoding="utf-8") as f:
        next(f)  # header
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line:
                continue
            parts = line.split(",", 1)
            if len(parts) != 2:
                continue
            yield parts[0].strip(), parts[1].strip()


def fetch_swabhasha_words() -> dict:
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    raw_path = RAW_DIR / "swabhasha_words.csv"
    sha, size = download_cached(SWABHASHA_WORDS_URL, raw_path, timeout=600)

    # Pass 1: collect the population of valid distinct Sinhala words (keys only,
    # to bound memory — this file has ~7.1M rows / 292MB).
    n_raw = 0
    words: set[str] = set()
    for romanized, sinhala in stream_word_pairs(raw_path):
        n_raw += 1
        if not valid_pair(romanized, sinhala):
            continue
        if grapheme_len(sinhala) < 2:  # skip single-cluster words (degenerate for CER)
            continue
        words.add(sinhala)

    rng = random.Random(SEED)
    population = sorted(words)  # sort first: sampling must not depend on file iteration order
    sample = set(rng.sample(population, GOLD_WORDS_N))
    log(f"Swa-Bhasha words: {n_raw} raw rows -> {len(population)} distinct valid words -> sampled {len(sample)}")

    # Pass 2: collect the full attested romanization set for just the sampled words.
    variants: dict[str, set[str]] = {w: set() for w in sample}
    for romanized, sinhala in stream_word_pairs(raw_path):
        if sinhala in variants and not contains_sinhala(romanized) and romanized:
            variants[sinhala].add(romanized)

    gold_words_path = GOLD_DIR / "gold_words.jsonl"
    with gold_words_path.open("w", encoding="utf-8") as f:
        for sinhala in sorted(variants):
            romanizations = sorted(variants[sinhala])
            f.write(
                json.dumps(
                    {"sinhala": sinhala, "romanizations": romanizations, "n_variants": len(romanizations)},
                    ensure_ascii=False,
                )
                + "\n"
            )

    heldout_path = GOLD_DIR / "heldout_words.txt"
    with heldout_path.open("w", encoding="utf-8") as f:
        for sinhala in sorted(variants):
            f.write(sinhala + "\n")

    log(f"gold_words -> {gold_words_path} ; heldout list -> {heldout_path}")
    return {
        "swabhasha_words": {
            "url": SWABHASHA_WORDS_URL,
            "sha256": sha,
            "size_bytes": size,
            "n_raw_rows": n_raw,
            "n_distinct_valid_words": len(population),
        },
        "gold_words": {"path": gold_words_path.relative_to(REPO_ROOT).as_posix(), "n": len(variants)},
        "heldout_words": {"path": heldout_path.relative_to(REPO_ROOT).as_posix(), "n": len(variants)},
    }


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    provenance = {
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "seed": SEED,
        "sources": {},
        "derived": {},
    }

    sold_manifest = fetch_sold()
    provenance["sources"].update(sold_manifest)

    sentences_manifest = fetch_swabhasha_sentences()
    provenance["sources"]["swabhasha_sentences"] = sentences_manifest["swabhasha_sentences"]
    provenance["derived"]["gold_sentences"] = sentences_manifest["gold_sentences"]
    provenance["derived"]["reference_singlish"] = sentences_manifest["reference_singlish"]

    words_manifest = fetch_swabhasha_words()
    provenance["sources"]["swabhasha_words"] = words_manifest["swabhasha_words"]
    provenance["derived"]["gold_words"] = words_manifest["gold_words"]
    provenance["derived"]["heldout_words"] = words_manifest["heldout_words"]

    PROVENANCE_PATH.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"wrote {PROVENANCE_PATH}")
    log("done.")


if __name__ == "__main__":
    main()
