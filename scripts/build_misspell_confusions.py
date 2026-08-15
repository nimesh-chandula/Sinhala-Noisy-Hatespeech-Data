"""
Phase 4a, Stage 1 — derive the Sinhala IME phonetic-collision confusion sets
that drive src/noisers/misspell.py's Channel A (see that module and LOG.md's
"Phase 4a" entry for the design rationale).

Most Sri Lankans type Sinhala through a phonetic IME on an English keyboard
(Helakuru, Google Sinhala Input): you type the roman spelling and the
keyboard picks the Sinhala grapheme. So a realistic misspelling isn't a
random key-adjacency slip — it's the IME resolving genuine ambiguity in the
roman->Sinhala mapping the wrong way. Two Sinhala grapheme clusters are
IME-confusable exactly when they romanize to the SAME string under the
Phase-1-winning backend (src/romanizers/aksharamukha.py's
romanize_colloquial) — so the confusion sets are DERIVED from that mapping
applied to every grapheme cluster actually occurring in SOLD, not hand-
guessed. Measured during planning: 767 distinct SOLD grapheme clusters ->
130 collision sets after dropping ZWJ/ZWNJ encoding artifacts and clusters
occurring fewer than FREQ_FLOOR times, covering 90% of Sinhala cluster
tokens in the corpus.

This script also freezes a single ATTESTATION VOCABULARY (SOLD's own word
types union the ~451K distinct Sinhala words in the Swa-Bhasha word list) —
the same "prefer attested, allow unattested" evidence source
src/noisers/misspell.py needs at generation time to decide, for a given
candidate substitution on a given word, whether the resulting form is a
real word or a plausible-but-unattested error. Built once here so the
noiser never touches the 292MB raw CSV.

Idempotent and rerunnable across review rounds, mirroring
scripts/build_codemix_wordbank.py's precedence-merge pattern: rerunning
after data/lexicon/misspell_review_corrections.jsonl gains more lines
(Stage 2) picks up the new corrections and regenerates everything from
scratch — there is no separate "apply corrections" step.

Writes:
  data/lexicon/misspell_confusions.jsonl       frozen sets the noiser reads
  data/lexicon/.misspell_confusions.sha256     hash, stamped into GENERATOR_VERSION
  data/lexicon/misspell_attested_vocab.txt     frozen attestation vocabulary
  data/lexicon/misspell_confusions_review.csv  for marking up corrections
  data/lexicon/misspell_confusions_review.md   for reading

Run:  python scripts/build_misspell_confusions.py
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import clusters, text_runs, ZWJ, ZWNJ  # noqa: E402
from src.romanizers.aksharamukha import romanize_colloquial  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
SOLD_DIR = DATA_DIR / "sold"
RAW_WORDS_PATH = DATA_DIR / "raw" / "swabhasha_words.csv"
LEXICON_DIR = DATA_DIR / "lexicon"

CONFUSIONS_PATH = LEXICON_DIR / "misspell_confusions.jsonl"
CONFUSIONS_HASH_PATH = LEXICON_DIR / ".misspell_confusions.sha256"
ATTESTED_VOCAB_PATH = LEXICON_DIR / "misspell_attested_vocab.txt"
CORRECTIONS_PATH = LEXICON_DIR / "misspell_review_corrections.jsonl"
REVIEW_CSV_PATH = LEXICON_DIR / "misspell_confusions_review.csv"
REVIEW_MD_PATH = LEXICON_DIR / "misspell_confusions_review.md"

# A cluster must occur at least this many times in SOLD train+test to be
# considered a real, in-vocabulary confusable — drops the long tail of
# singleton/near-singleton clusters that turned out on inspection to be
# stray encoding artifacts already present in SOLD's raw scraped text, not
# genuine IME-confusable graphemes (measured: 767 clusters -> 130 sets at
# floor=5, still covering 90% of Sinhala cluster tokens).
FREQ_FLOOR = 5
MAX_EXAMPLES = 3


def log(msg: str) -> None:
    print(f"[build_misspell_confusions] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def sold_word_and_cluster_freq() -> tuple[Counter, Counter]:
    """(word_freq, cluster_freq) over every Sinhala run in SOLD train+test —
    word_freq keyed by whole word (for attestation/example lookups),
    cluster_freq keyed by individual grapheme cluster (for the collision
    grouping and the frequency floor)."""
    word_freq: Counter = Counter()
    cluster_freq: Counter = Counter()
    for split in ("train", "test"):
        with (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                text = json.loads(line)["text"]
                for is_sinhala, run in text_runs(text):
                    if not is_sinhala:
                        continue
                    word_freq[run] += 1
                    for c in clusters(run):
                        cluster_freq[c] += 1
    return word_freq, cluster_freq


def swabhasha_vocab() -> set[str]:
    """Distinct Sinhala words from the Swa-Bhasha word-pair source (same raw
    file scripts/build_word_variants.py streams) — a second, much larger
    attestation source than SOLD alone. ~451K distinct words, ~10s to
    stream. Every row is (RomanizedSinhala, Sinhala); only the Sinhala
    column is used here."""
    vocab: set[str] = set()
    if not RAW_WORDS_PATH.exists():
        log(f"WARNING: {RAW_WORDS_PATH} not found — attestation will use SOLD only")
        return vocab
    with RAW_WORDS_PATH.open("r", encoding="utf-8") as f:
        next(f)  # header
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line:
                continue
            parts = line.split(",", 1)
            if len(parts) != 2:
                continue
            sinhala = parts[1].strip()
            if sinhala:
                vocab.add(sinhala)
    return vocab


def _consonant_signature(cluster_str: str) -> str:
    """`cluster_str` with dependent vowel signs stripped, virama/ZWJ/ZWNJ
    kept — i.e. "which base consonant (and open/closed syllable state)",
    ignoring which vowel is attached. Used to classify a confusion set as
    vowel-length (same signature across members) vs consonant-quality
    (same vowel signature, different consonant signature)."""
    return "".join(
        ch for ch in cluster_str
        if not (unicodedata.category(ch) in ("Mn", "Mc") and ch not in ("්", ZWJ, ZWNJ))
    )


def _vowel_signature(cluster_str: str) -> str:
    """The dependent vowel signs stripped out by _consonant_signature —
    empty for a bare/inherent-vowel or pure-consonant (virama) cluster."""
    return "".join(
        ch for ch in cluster_str
        if unicodedata.category(ch) in ("Mn", "Mc") and ch not in ("්", ZWJ, ZWNJ)
    )


def classify_set(members: list[str]) -> str:
    csigs = {_consonant_signature(c) for c in members}
    vsigs = {_vowel_signature(c) for c in members}
    if len(csigs) == 1:
        return "vowel_length"
    if len(vsigs) == 1:
        return "consonant_quality"
    return "mixed"


def derive_raw_sets(cluster_freq: Counter) -> dict[str, list[str]]:
    """{romanization_key: [cluster, ...]} for every romanization that >=2
    SOLD-attested (>=FREQ_FLOOR occurrences), non-ZWJ/ZWNJ clusters collide
    on. This is the pure derivation step — no review corrections applied
    yet (see merge_corrections())."""
    by_rom: dict[str, list[str]] = defaultdict(list)
    for c, freq in cluster_freq.items():
        if freq < FREQ_FLOOR:
            continue
        if ZWJ in c or ZWNJ in c:
            continue
        by_rom[romanize_colloquial(c)].append(c)
    return {k: sorted(v, key=lambda c: -cluster_freq[c]) for k, v in by_rom.items() if len(v) > 1}


def merge_corrections(raw_sets: dict[str, list[str]]) -> tuple[dict[str, list[str]], int, int]:
    """Apply data/lexicon/misspell_review_corrections.jsonl on top of the
    raw derivation. Two actions, mirroring build_codemix_wordbank.py's
    precedence-merge shape:
      - {"key": ..., "action": "reject_set"}: drop the whole set.
      - {"key": ..., "action": "remove_members", "remove": [cluster, ...]}:
        drop specific members; if fewer than 2 remain, the set is dropped
        entirely (a 1-member "confusion set" is not a confusion).
    Corrections accumulate across rounds (append-only file); if the same
    key is corrected twice, the LAST line wins, matching every other
    corrections-merge script in this repo.
    """
    sets = {k: list(v) for k, v in raw_sets.items()}
    n_rejected = n_trimmed = 0
    for row in _load_jsonl(CORRECTIONS_PATH):
        key = row["key"]
        action = row["action"]
        if action == "reject_set":
            if sets.pop(key, None) is not None:
                n_rejected += 1
            continue
        if action == "remove_members":
            if key not in sets:
                continue
            remove = set(row["remove"])
            kept = [c for c in sets[key] if c not in remove]
            if len(kept) < 2:
                sets.pop(key, None)
                n_rejected += 1
            else:
                sets[key] = kept
                n_trimmed += 1
            continue
        raise ValueError(f"unknown correction action {action!r} for key {key!r}")
    return sets, n_rejected, n_trimmed


def _is_attested(word: str, attested_vocab: set[str]) -> bool:
    return word in attested_vocab


def build_pair_examples(
    sets: dict[str, list[str]],
    word_freq: Counter,
    attested_vocab: set[str],
) -> tuple[dict[str, int], dict[str, list[tuple[str, str, bool]]]]:
    """For every set, walk SOLD's word vocabulary once and collect:
      - impact[key]: sum of word-token frequency touched by >=1 member of
        the set (how many real corpus tokens this set could ever alter)
      - examples[key]: up to MAX_EXAMPLES (original_word, misspelled_word,
        is_attested) samples, highest-frequency word first, for the human
        review file.
    """
    cluster_to_key = {c: key for key, members in sets.items() for c in members}
    impact: Counter = Counter()
    examples: dict[str, list[tuple[str, str, bool]]] = defaultdict(list)

    for word, freq in sorted(word_freq.items(), key=lambda kv: -kv[1]):
        cs = clusters(word)
        touched_keys: set[str] = set()
        for i, c in enumerate(cs):
            key = cluster_to_key.get(c)
            if key is None:
                continue
            touched_keys.add(key)
            if len(examples[key]) >= MAX_EXAMPLES:
                continue
            members = sets[key]
            # Pick the first other member (deterministic: members is
            # frequency-sorted) to illustrate the substitution.
            other = next((m for m in members if m != c), None)
            if other is None:
                continue
            new_word = "".join(cs[:i] + [other] + cs[i + 1:])
            examples[key].append((word, new_word, _is_attested(new_word, attested_vocab)))
        for key in touched_keys:
            impact[key] += freq

    return dict(impact), dict(examples)


def main() -> None:
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)

    word_freq, cluster_freq = sold_word_and_cluster_freq()
    log(f"SOLD: {len(word_freq)} distinct Sinhala word types, "
        f"{len(cluster_freq)} distinct grapheme clusters, "
        f"{sum(cluster_freq.values())} cluster tokens total")

    raw_sets = derive_raw_sets(cluster_freq)
    log(f"derived {len(raw_sets)} raw romanization-collision sets "
        f"(freq>={FREQ_FLOOR}, ZWJ/ZWNJ excluded)")

    sets, n_rejected, n_trimmed = merge_corrections(raw_sets)
    corrections = _load_jsonl(CORRECTIONS_PATH)
    if corrections:
        log(f"applied {len(corrections)} review corrections: "
            f"{n_rejected} sets rejected, {n_trimmed} sets trimmed")
    log(f"-> {len(sets)} confusion sets after corrections")

    sw_vocab = swabhasha_vocab()
    log(f"Swa-Bhasha vocabulary: {len(sw_vocab)} distinct Sinhala words")
    attested_vocab = set(word_freq) | sw_vocab
    log(f"attestation vocabulary (SOLD + Swa-Bhasha): {len(attested_vocab)} words")

    covered_tokens = sum(cluster_freq[c] for members in sets.values() for c in members)
    log(f"cluster-token coverage: {covered_tokens}/{sum(cluster_freq.values())} "
        f"({100 * covered_tokens / sum(cluster_freq.values()):.1f}%)")

    impact, examples = build_pair_examples(sets, word_freq, attested_vocab)

    # --- write frozen artifacts the noiser reads at generation time ---
    type_by_key = {key: classify_set(members) for key, members in sets.items()}
    rows_out = []
    for key in sorted(sets):
        members = sets[key]
        rows_out.append({
            "key": key,
            "type": type_by_key[key],
            "members": members,
            "member_freq": {c: cluster_freq[c] for c in members},
        })
    with CONFUSIONS_PATH.open("w", encoding="utf-8") as f:
        for row in rows_out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    digest = hashlib.sha256(CONFUSIONS_PATH.read_bytes()).hexdigest()
    CONFUSIONS_HASH_PATH.write_text(digest, encoding="utf-8")
    log(f"wrote {len(rows_out)} confusion sets -> {CONFUSIONS_PATH}")
    log(f"sha256={digest} (first 8: {digest[:8]}) -> {CONFUSIONS_HASH_PATH}")

    with ATTESTED_VOCAB_PATH.open("w", encoding="utf-8") as f:
        for w in sorted(attested_vocab):
            f.write(w + "\n")
    log(f"wrote {len(attested_vocab)} words -> {ATTESTED_VOCAB_PATH}")

    # --- write human review artifacts, impact-ordered ---
    ordered_keys = sorted(sets, key=lambda k: (-impact.get(k, 0), k))

    with REVIEW_CSV_PATH.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "key", "type", "members", "impact_tokens",
            "example_1_before", "example_1_after", "example_1_attested",
            "example_2_before", "example_2_after", "example_2_attested",
            "example_3_before", "example_3_after", "example_3_attested",
            "verdict", "remove_members", "notes",
        ])
        writer.writeheader()
        for key in ordered_keys:
            flat = {}
            exs = examples.get(key, [])
            for i in range(MAX_EXAMPLES):
                before, after, attested = exs[i] if i < len(exs) else ("", "", "")
                flat[f"example_{i + 1}_before"] = before
                flat[f"example_{i + 1}_after"] = after
                flat[f"example_{i + 1}_attested"] = attested
            writer.writerow({
                "key": key,
                "type": type_by_key[key],
                "members": " / ".join(sets[key]),
                "impact_tokens": impact.get(key, 0),
                **flat,
                "verdict": "", "remove_members": "", "notes": "",
            })
    log(f"wrote review CSV -> {REVIEW_CSV_PATH}")

    lines = [
        "# Misspelling confusion-set review",
        "",
        f"{len(ordered_keys)} romanization-collision sets, impact-ordered by how many "
        "Sinhala word-tokens in SOLD contain >=1 member cluster (i.e. how much of the "
        "corpus this set could ever touch). Each set is a group of Sinhala grapheme "
        "clusters that a phonetic IME (type the roman spelling, get the Sinhala "
        "character) cannot distinguish between — see src/noisers/misspell.py and "
        "LOG.md's Phase 4a entry for why that's the misspelling mechanism modeled here.",
        "",
        "For each set: reject the whole set (`reject_set`) if the confusion isn't "
        "something a real typist would actually produce, or list specific clusters "
        "to drop (`remove_members`) if only some members are implausible. Leave both "
        "blank to accept as-is. Record corrections in "
        "data/lexicon/misspell_review_corrections.jsonl "
        "(one JSON line per set: {\"key\": ..., \"action\": \"reject_set\"} or "
        "{\"key\": ..., \"action\": \"remove_members\", \"remove\": [...]}).",
        "",
    ]
    for i, key in enumerate(ordered_keys, 1):
        members = sets[key]
        rtype = type_by_key[key]
        lines.append(f"## {i}. `{key}` ({rtype}) — {' / '.join(members)}")
        lines.append(f"- impact: {impact.get(key, 0)} word-tokens in SOLD")
        lines.append(f"- members by frequency: " + ", ".join(f"{c} ({cluster_freq[c]})" for c in members))
        for before, after, attested in examples.get(key, []):
            flag = "attested" if attested else "unattested"
            lines.append(f"  - `{before}` -> `{after}` ({flag})")
        lines.append("")
    REVIEW_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    log(f"wrote review MD -> {REVIEW_MD_PATH}")


if __name__ == "__main__":
    main()
