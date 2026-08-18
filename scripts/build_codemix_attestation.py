"""
Code-mix bank correction round 4 — evidence base for an ATTESTATION-AWARE
selection redesign (see the approved plan's addendum: "detect genuine
code-mixes, understand where they occur, use that knowledge in an
explainable way").

Builds a per-word EVIDENCE index: for every English headword that could be
a code-mix target, how much real proof exists that a Sinhala-speaking writer
actually switches to it, ranked by how trustworthy that proof is. Three tiers,
strongest first:

  PRIMARY   — extracted fresh from data/sold/{train,test}.jsonl: a Latin-script
              token with a Sinhala grapheme-cluster run on BOTH sides
              (src.graphemes.text_runs), i.e. an English word sitting inside a
              real Sinhala sentence written by a real person. This is the
              exact phenomenon the noiser is supposed to imitate, in the exact
              register (SOLD tweets) the noiser is applied to.
  SECONDARY — data/lexicon/codemix_reference_stats.json's
              eka_construction_vocabulary: English stems observed directly
              attached to a Sinhala "එක" case particle in SOLD's raw text —
              the exact construction this noiser's word bank encodes for many
              entries (e.g. "government එක"), mined independently by
              scripts/measure_codemix_rate.py.
  TERTIARY  — the same file's candidate_english_vocabulary: Latin tokens not
              attested as any Sinhala word's romanization, pooled across SOLD
              and the reference_singlish corpus. Broadest reach, weakest
              precision (includes scrape artifacts, quoted English, etc. that
              slipped past the SOLD-cleaning step) — used only to widen
              recall when nothing stronger is available.

This script is READ-ONLY with respect to the lexicon: it does not edit
codemix_wordbank.jsonl. It writes one new evidence artifact.

Writes:
  data/lexicon/codemix_attested_vocabulary.json
    {headword_lowercase: {"tier": "primary"|"secondary"|"tertiary",
                           "count": int, "examples": [sentence, ...]}}
  data/lexicon/.codemix_attested_vocabulary.sha256
    hash sidecar, same convention as .codemix_wordbank.sha256 -- both files
    now drive src.noisers.codemix's selection, so a rebuild of EITHER must
    be visible in GENERATOR_VERSION (golden rule 4: determinism + drift
    visibility). See that module's _wordbank_version_suffix() /
    _attested_version_suffix().

Run:  python scripts/build_codemix_attestation.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

SOLD_DIR = REPO_ROOT / "data" / "sold"
LEXICON_DIR = REPO_ROOT / "data" / "lexicon"
REFERENCE_STATS_PATH = LEXICON_DIR / "codemix_reference_stats.json"
OUT_PATH = LEXICON_DIR / "codemix_attested_vocabulary.json"
HASH_PATH = LEXICON_DIR / ".codemix_attested_vocabulary.sha256"

_SKIP_HEADWORDS = {"url", "user", "rt", "lka", "srilanka", "lanka", "sri"}
_LATIN_WORD_RE = re.compile(r"^[A-Za-z][A-Za-z\-]{1,}$")
_SINHALA_WORD_RE = re.compile(r"^[඀-෿‍]+$")
_STRIP_CHARS = ".,!?\"'()[]{}#@:;‘’“”"


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _mine_primary() -> tuple[dict[str, int], dict[str, list[str]]]:
    """Whitespace-token scan: a Latin word with a Sinhala-only word
    immediately before AND after it, i.e. an English word sitting inside a
    real Sinhala sentence written by a real person. Deliberately
    whitespace-based rather than src.graphemes.text_runs: text_runs merges
    a word with its surrounding whitespace into one non-Sinhala run
    (`' thanks '`), which is the right unit for the noiser's own
    substitution logic but the wrong unit for "what word came right before/
    after this one" — this needs word boundaries, not script-run boundaries."""
    counts: dict[str, int] = defaultdict(int)
    examples: dict[str, list[str]] = defaultdict(list)
    for split in ("train", "test"):
        for row in _load_jsonl(SOLD_DIR / f"{split}.jsonl"):
            text = row["text"]
            words = [w.strip(_STRIP_CHARS) for w in text.split()]
            for i in range(1, len(words) - 1):
                token = words[i]
                if not _LATIN_WORD_RE.match(token):
                    continue
                key = token.lower()
                if key in _SKIP_HEADWORDS:
                    continue
                if _SINHALA_WORD_RE.match(words[i - 1]) and _SINHALA_WORD_RE.match(words[i + 1]):
                    counts[key] += 1
                    if len(examples[key]) < 3:
                        examples[key].append(text)
    return dict(counts), dict(examples)


def main() -> None:
    print("[build_codemix_attestation] mining PRIMARY evidence from SOLD...")
    primary_counts, primary_examples = _mine_primary()
    print(f"[build_codemix_attestation] primary: {len(primary_counts)} distinct types, "
          f"{sum(primary_counts.values())} instances")

    ref_stats = json.loads(REFERENCE_STATS_PATH.read_text(encoding="utf-8")) if REFERENCE_STATS_PATH.exists() else {}
    secondary = {row["token"].lower(): row["count"] for row in ref_stats.get("eka_construction_vocabulary", [])}
    tertiary = {row["token"].lower(): row["count"] for row in ref_stats.get("candidate_english_vocabulary", [])}
    print(f"[build_codemix_attestation] secondary (eka-construction): {len(secondary)} types")
    print(f"[build_codemix_attestation] tertiary (candidate vocabulary): {len(tertiary)} types")

    vocabulary: dict[str, dict] = {}
    all_keys = set(primary_counts) | set(secondary) | set(tertiary)
    for key in all_keys:
        if key in primary_counts:
            tier, count, examples = "primary", primary_counts[key], primary_examples[key]
        elif key in secondary:
            tier, count, examples = "secondary", secondary[key], []
        else:
            tier, count, examples = "tertiary", tertiary[key], []
        vocabulary[key] = {"tier": tier, "count": count, "examples": examples}

    OUT_PATH.write_text(json.dumps(vocabulary, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(f"[build_codemix_attestation] wrote {len(vocabulary)} evidence entries -> {OUT_PATH}")
    print(f"[build_codemix_attestation]   primary={sum(1 for v in vocabulary.values() if v['tier']=='primary')} "
          f"secondary={sum(1 for v in vocabulary.values() if v['tier']=='secondary')} "
          f"tertiary={sum(1 for v in vocabulary.values() if v['tier']=='tertiary')}")

    digest = hashlib.sha256(OUT_PATH.read_bytes()).hexdigest()
    HASH_PATH.write_text(digest, encoding="utf-8")
    print(f"[build_codemix_attestation] sha256={digest} (first 8: {digest[:8]}) -> {HASH_PATH}")


if __name__ == "__main__":
    main()
