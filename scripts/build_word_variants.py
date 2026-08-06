"""
Build a Sinhala-word -> [attested romanization variants] lookup for the
transliteration noiser's severity mechanism (src/noisers/transliteration.py).

Severity there is spelling-variance intensity: "heavy" substitutes a real,
attested alternate spelling for more words than "light" does, mimicking a
more casual/inconsistent typist. The variants come from the same Swa-Bhasha
word-level source data/gold/gold_words.jsonl was built from
(data/raw/swabhasha_words.csv, already cached — no new download).

Two things keep this a SOLD-scale lookup instead of a 450K-word one:
  1. Only words that actually appear in SOLD's text (train+test) are looked
     up — the full Swa-Bhasha vocabulary is far larger than anything this
     project will ever transliterate.
  2. The 2000 words in data/gold/heldout_words.txt are excluded — built in
     Phase 0 for exactly this situation, so generation never leaks the CER
     gold set's answers into itself.

A third filter, added after a spot-check surfaced a bad entry: some
Swa-Bhasha word-pairs are simply wrong (e.g. "සර්" (sar/"sir") listed
"pathi" — an unrelated word meaning "husband/lord" — among its attested
romanizations). Legitimate spelling variants stay close to the canonical
romanization (measured CER 0.0-0.67 against real variants like "ser"/"sir"/
"sr" for "සර්"), while bad entries are far off (CER >= 1.33 for "pathi").
Each candidate variant is kept only if its grapheme-cluster CER against the
canonical Phase-1 romanization is <= MAX_VARIANT_CER.

A fourth filter, added after a manual review of a 100-item sample surfaced
a case the CER filter missed: "තුල" (canonical "thula") was noised to
"lthula" — CER("lthula", "thula")=0.2, well under the 0.7 threshold,
because a single character *insertion* on an otherwise-correct word scores
deceptively low. Real casual spelling variance essentially never changes a
word's first letter (people drop trailing vowels, double letters, etc. —
they don't insert/change what the word starts with), so each candidate
variant must also share its first character with canonical. Verified this
doesn't conflict with legitimate loanword-recovery variants (e.g.
"අප්ඩේට්"'s attested "update" vs. a mis-transliterated canonical) because
src/romanizers/aksharamukha.py now corrects loanwords at the canonical
level *before* this script runs — canonical is already "update" by the
time this filter sees it, so the first letters match correctly.

Run:  python scripts/build_word_variants.py
Writes data/lexicon/word_variants.jsonl: {"sinhala": ..., "romanizations": [...]}
one line per SOLD-vocabulary word that has at least one attested,
CER-filtered variant (besides the canonical romanization, which is computed
at generation time, not stored here).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import contains_sinhala, text_runs  # noqa: E402
from src.romanizers.aksharamukha import romanize_colloquial  # noqa: E402
from eval.gold_cer import cer  # noqa: E402

MAX_VARIANT_CER = 0.7

DATA_DIR = REPO_ROOT / "data"
SOLD_DIR = DATA_DIR / "sold"
RAW_WORDS_PATH = DATA_DIR / "raw" / "swabhasha_words.csv"
HELDOUT_PATH = DATA_DIR / "gold" / "heldout_words.txt"
LEXICON_DIR = DATA_DIR / "lexicon"
OUTPUT_PATH = LEXICON_DIR / "word_variants.jsonl"


def log(msg: str) -> None:
    print(f"[build_word_variants] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sold_vocabulary() -> set[str]:
    """Distinct Sinhala words appearing anywhere in SOLD train+test text."""
    vocab: set[str] = set()
    for split in ("train", "test"):
        for row in _load_jsonl(SOLD_DIR / f"{split}.jsonl"):
            for is_sinhala, run in text_runs(row["text"]):
                if is_sinhala:
                    vocab.add(run)
    return vocab


def stream_word_pairs(path: Path):
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


def main() -> None:
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)

    vocab = sold_vocabulary()
    heldout = {line.strip() for line in HELDOUT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()}
    lookup_words = vocab - heldout
    log(f"SOLD vocabulary: {len(vocab)} distinct Sinhala words; "
        f"{len(heldout)} held out (Phase 0 gold set); {len(lookup_words)} eligible for lookup")

    variants: dict[str, set[str]] = {w: set() for w in lookup_words}
    n_raw = 0
    for romanized, sinhala in stream_word_pairs(RAW_WORDS_PATH):
        n_raw += 1
        if sinhala in variants and romanized and not contains_sinhala(romanized):
            variants[sinhala].add(romanized)
    log(f"streamed {n_raw} raw word-pairs")

    # CER-filter against the canonical Phase-1 romanization (see module
    # docstring — catches wrong entries like "සර්" -> "pathi"). The
    # canonical spelling itself is deliberately EXCLUDED from the stored
    # list: these are substitutes offered to the noiser as alternates, not
    # a menu that includes "no change" — that keeps realised_noise_rate a
    # clean, predictable function of how often a substitution is offered.
    n_filtered_out = 0
    multi_variant: dict[str, list[str]] = {}
    for word, raw_variants in variants.items():
        if not raw_variants:
            continue
        canonical = romanize_colloquial(word)
        kept = [
            v for v in raw_variants
            if v != canonical
            and cer(v, canonical) <= MAX_VARIANT_CER
            and v[:1].lower() == canonical[:1].lower()
        ]
        n_filtered_out += len(raw_variants) - len(kept)
        if kept:
            multi_variant[word] = sorted(kept)
    log(f"CER/first-letter-filtered out {n_filtered_out} bad/canonical-duplicate variant entries "
        f"(CER > {MAX_VARIANT_CER}, == canonical, or different first letter)")
    log(f"{len(multi_variant)}/{len(lookup_words)} SOLD words have >=1 attested alternate spelling after filtering")

    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for word in sorted(multi_variant):
            f.write(json.dumps({"sinhala": word, "romanizations": multi_variant[word]}, ensure_ascii=False) + "\n")
    log(f"wrote {len(multi_variant)} entries -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
