"""
Hard pass/fail invariants. Every one must return True to proceed.

Phase 0 implements checks over what currently exists: the gold/reference
corpora, the SOLD splits, the schema module, and the throwaway stub
romanizer. Checks whose subject doesn't exist yet (e.g. split_isolation,
which needs Phase 5's noised outputs) return True VACUOUSLY — but that must
never look like a silent pass, so `run_invariants()` is paired with
`invariant_notes()`, which the harness renders alongside every result.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import contains_sinhala, is_lossless  # noqa: E402
from src.schema import Row  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
GOLD_DIR = DATA_DIR / "gold"
REFERENCE_PATH = DATA_DIR / "reference" / "reference_singlish.txt"
SOLD_DIR = DATA_DIR / "sold"

EXPECTED_SOLD_ROWS = {"train": 7500, "test": 2500}
EXPECTED_TOTAL_ROWS = 10000
EXPECTED_OFF_RATE_BAND = (0.35, 0.45)

# Notes for any check whose result needs context beyond pass/fail — most
# importantly, marks the ones that are vacuously true because their subject
# doesn't exist yet. Populated by the check functions as they run.
_notes: dict[str, str] = {}


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [line.rstrip("\n") for line in f if line.strip()]


# ---------------------------------------------------------------------------
# Gold / reference corpus checks
# ---------------------------------------------------------------------------

def check_gold_sets_present() -> bool:
    """data/gold/{gold_words,gold_sentences}.jsonl exist and are non-empty."""
    words = _load_jsonl(GOLD_DIR / "gold_words.jsonl")
    sentences = _load_jsonl(GOLD_DIR / "gold_sentences.jsonl")
    ok = bool(words) and bool(sentences)
    if not ok:
        _notes["gold_sets_present"] = f"gold_words={len(words)} gold_sentences={len(sentences)}"
    return ok


def check_reference_corpus_present() -> bool:
    """data/reference/reference_singlish.txt exists and is non-empty."""
    lines = _load_lines(REFERENCE_PATH)
    ok = len(lines) > 0
    if not ok:
        _notes["reference_corpus_present"] = "reference_singlish.txt missing or empty"
    return ok


def check_gold_reference_disjoint() -> bool:
    """No romanized string in the CER gold set also appears in the realism
    reference corpus — otherwise realism scoring is contaminated by strings
    the harness has already seen as ground truth."""
    gold_sentences = _load_jsonl(GOLD_DIR / "gold_sentences.jsonl")
    reference = _load_lines(REFERENCE_PATH)
    if not gold_sentences or not reference:
        _notes["gold_reference_disjoint"] = "vacuous: gold or reference not yet present"
        return True
    gold_set = {row["romanized"] for row in gold_sentences}
    ref_set = set(reference)
    overlap = gold_set & ref_set
    ok = not overlap
    if not ok:
        _notes["gold_reference_disjoint"] = f"{len(overlap)} strings leak between gold and reference"
    return ok


def check_gold_romanized_side_has_no_sinhala() -> bool:
    """The romanized side of every gold pair must be free of Sinhala codepoints."""
    sentences = _load_jsonl(GOLD_DIR / "gold_sentences.jsonl")
    words = _load_jsonl(GOLD_DIR / "gold_words.jsonl")
    bad = [row["romanized"] for row in sentences if contains_sinhala(row["romanized"])]
    bad += [
        rom
        for row in words
        for rom in row["romanizations"]
        if contains_sinhala(rom)
    ]
    ok = not bad
    if not ok:
        _notes["gold_romanized_side_has_no_sinhala"] = f"{len(bad)} romanized entries contain Sinhala"
    return ok


def check_gold_sinhala_side_has_sinhala() -> bool:
    """The Sinhala side of every gold pair must actually contain Sinhala codepoints."""
    sentences = _load_jsonl(GOLD_DIR / "gold_sentences.jsonl")
    words = _load_jsonl(GOLD_DIR / "gold_words.jsonl")
    bad = [row["sinhala"] for row in sentences if not contains_sinhala(row["sinhala"])]
    bad += [row["sinhala"] for row in words if not contains_sinhala(row["sinhala"])]
    ok = not bad
    if not ok:
        _notes["gold_sinhala_side_has_sinhala"] = f"{len(bad)} 'sinhala' entries contain no Sinhala"
    return ok


def check_grapheme_roundtrip_lossless() -> bool:
    """clusters(text) must always rejoin to exactly `text` — clustering groups
    codepoints, it must never drop or reorder them. Checked over all gold
    Sinhala text (real-world conjuncts, vowel signs, ZWJ)."""
    sentences = _load_jsonl(GOLD_DIR / "gold_sentences.jsonl")
    words = _load_jsonl(GOLD_DIR / "gold_words.jsonl")
    samples = [row["sinhala"] for row in sentences] + [row["sinhala"] for row in words]
    if not samples:
        _notes["grapheme_roundtrip_lossless"] = "vacuous: no gold Sinhala text to check yet"
        return True
    bad = [s for s in samples if not is_lossless(s)]
    ok = not bad
    if not ok:
        _notes["grapheme_roundtrip_lossless"] = f"{len(bad)}/{len(samples)} samples failed round-trip"
    return ok


# ---------------------------------------------------------------------------
# SOLD checks
# ---------------------------------------------------------------------------

def check_sold_counts_match_paper() -> bool:
    """Persisted data/sold/{train,test}.jsonl match the SOLD paper's reported
    counts (~10k total) and offensive rate (~41%). Independent of
    scripts/fetch_data.py's own assertions — re-verifies the committed data,
    catching any manual edit or corruption after the fact."""
    train = _load_jsonl(SOLD_DIR / "train.jsonl")
    test = _load_jsonl(SOLD_DIR / "test.jsonl")
    if not train or not test:
        _notes["sold_counts_match_paper"] = "vacuous: data/sold/*.jsonl not yet present"
        return True
    if len(train) != EXPECTED_SOLD_ROWS["train"] or len(test) != EXPECTED_SOLD_ROWS["test"]:
        _notes["sold_counts_match_paper"] = f"train={len(train)} test={len(test)}, expected {EXPECTED_SOLD_ROWS}"
        return False
    total = len(train) + len(test)
    off_rate = (sum(r["label"] for r in train) + sum(r["label"] for r in test)) / total
    lo, hi = EXPECTED_OFF_RATE_BAND
    ok = total == EXPECTED_TOTAL_ROWS and lo <= off_rate <= hi
    if not ok:
        _notes["sold_counts_match_paper"] = f"total={total}, off_rate={off_rate:.3f}, expected band {EXPECTED_OFF_RATE_BAND}"
    return ok


def check_sold_split_disjoint() -> bool:
    """No post_id appears in both data/sold/train.jsonl and test.jsonl."""
    train = _load_jsonl(SOLD_DIR / "train.jsonl")
    test = _load_jsonl(SOLD_DIR / "test.jsonl")
    if not train or not test:
        _notes["sold_split_disjoint"] = "vacuous: data/sold/*.jsonl not yet present"
        return True
    overlap = {r["post_id"] for r in train} & {r["post_id"] for r in test}
    ok = not overlap
    if not ok:
        _notes["sold_split_disjoint"] = f"{len(overlap)} post_ids appear in both splits"
    return ok


# ---------------------------------------------------------------------------
# Schema / pipeline checks
# ---------------------------------------------------------------------------

def check_schema_validates() -> bool:
    """src.schema.Row.validate() accepts a well-formed row and rejects an
    empty noisy_text, per its own contract."""
    good = Row(
        source_id="123", split="train", condition="clean", severity="none",
        original_text="hello", noisy_text="hello", label=0,
        realised_noise_rate=0.0, generator_version="phase1-schema-check",
    )
    try:
        good.validate()
    except AssertionError:
        _notes["schema_validates"] = "a well-formed Row failed validate()"
        return False

    bad = Row(
        source_id="123", split="train", condition="clean", severity="none",
        original_text="hello", noisy_text="   ", label=0,
        realised_noise_rate=0.0, generator_version="phase1-schema-check",
    )
    try:
        bad.validate()
    except AssertionError:
        return True
    _notes["schema_validates"] = "Row.validate() accepted an empty noisy_text"
    return False


def check_no_empty_outputs() -> bool:
    """No romanized output may be empty or whitespace-only. Checked against
    every registered Phase 1 backend (eval.gold_cer.discover_backends) over
    the gold-words sample; Phase 2+ re-runs this over real noiser output."""
    words = _load_jsonl(GOLD_DIR / "gold_words.jsonl")
    if not words:
        _notes["no_empty_outputs"] = "vacuous: no gold sample to run backends over yet"
        return True
    from eval.gold_cer import discover_backends

    backends = discover_backends()
    if not backends:
        _notes["no_empty_outputs"] = "vacuous: no romanizer backend available yet"
        return True
    bad = {}
    for name, fn in backends.items():
        empties = [row["sinhala"] for row in words if not fn(row["sinhala"]).strip()]
        if empties:
            bad[name] = len(empties)
    ok = not bad
    if not ok:
        _notes["no_empty_outputs"] = f"empty outputs by backend: {bad} (of {len(words)} words)"
    return ok


def check_determinism() -> bool:
    """Same input + same backend/noiser => identical output, run twice.
    Checked against every registered Phase 1 backend (no RNG in any of
    them), AND against every implemented Phase 2+ noiser at a fixed seed
    (per this check's own long-standing TODO) — a noiser's determinism
    can't be assumed the way a backend's can, since it consumes a
    random.Random(seed) internally."""
    words = _load_jsonl(GOLD_DIR / "gold_words.jsonl")
    if not words:
        _notes["determinism"] = "vacuous: no sample to check determinism over yet"
        return True

    bad = []
    skipped = []

    from eval.gold_cer import discover_backends_with_status

    backends, backends_unavailable = discover_backends_with_status()
    if not backends:
        _notes["determinism"] = "vacuous: no romanizer backend available yet"
        return True
    sample = [row["sinhala"] for row in words[:50]]
    for name, fn in backends.items():
        run1 = [fn(s) for s in sample]
        run2 = [fn(s) for s in sample]
        if run1 != run2:
            bad.append(name)
    skipped.extend(f"backend:{name}" for name in backends_unavailable)

    import importlib

    noiser_sample = [row["sinhala"] for row in words[:20]]
    # NOTE: an ImportError here used to be swallowed with a bare `continue`,
    # which let this invariant report green while silently never having
    # checked a noiser at all (caught when eval/report.json's committed run
    # turned out to have skipped transliteration's determinism check
    # entirely because aksharamukha wasn't installed in that interpreter —
    # see Stage 0 in LOG.md). Any skip is now recorded in `skipped` and
    # surfaced via invariant_notes so a green run can't hide it again.
    for noiser_name in ("transliteration", "codemix", "misspell", "abbreviate"):
        try:
            module = importlib.import_module(f"src.noisers.{noiser_name}")
        except ImportError as e:
            skipped.append(f"noiser:{noiser_name} ({e})")
            continue
        target_rates = getattr(module, "TARGET_NOISE_RATE", {})
        if not target_rates:
            skipped.append(f"noiser:{noiser_name} (not implemented / no TARGET_NOISE_RATE)")
            continue
        for severity in target_rates:
            try:
                run1 = [module.apply(t, severity, seed=1337) for t in noiser_sample]
                run2 = [module.apply(t, severity, seed=1337) for t in noiser_sample]
            except NotImplementedError:
                skipped.append(f"noiser:{noiser_name}/{severity} (not implemented)")
                continue
            if run1 != run2:
                bad.append(f"{noiser_name}/{severity}")

    ok = not bad
    note_parts = []
    if not ok:
        note_parts.append(f"non-deterministic backends/noisers: {bad}")
    if skipped:
        note_parts.append(f"skipped (not available in this interpreter): {skipped}")
    if note_parts:
        _notes["determinism"] = "; ".join(note_parts)
    return ok


def check_grapheme_integrity() -> bool:
    """No noiser output may split a Sinhala grapheme cluster mid-syllable —
    checked over every row's noisy_text in data/outputs/{train,test}/*.jsonl,
    via is_lossless() (a clean cluster round-trip) and
    starts_with_combining() (a cluster beginning with a combining mark or
    ZWJ/ZWNJ is definitionally a mid-syllable split). noisy_text won't
    always contain Sinhala (transliteration output is pure Latin) — when it
    doesn't, there's simply nothing to fail on; when it does (codemix
    deliberately keeps most of a post in Sinhala script), it must stay
    grapheme-safe exactly like the original.

    A combining-starting cluster already present verbatim in original_text
    is INHERITED, not introduced by noising, and must not fail this check —
    SOLD's own raw scraped text has 4 posts with a stray leading ZWJ/ZWNJ
    (an artifact of however the tweets were originally captured, wholly
    unrelated to this pipeline), and every noiser passes non-Sinhala runs
    through unchanged, so that leading character propagates into noisy_text
    verbatim. Faithfully preserving it is correct — the same principle
    already established for a source typo in Phase 2's GATE A review (see
    LOG.md: fixing it would mean silently editing SOLD's original text,
    which is out of scope for a noising pipeline). Only a NEW
    combining-start cluster not present in original_text is a real failure."""
    from src.graphemes import clusters, starts_with_combining

    outputs_dir = REPO_ROOT / "data" / "outputs"
    checked = 0
    bad = []
    for split in ("train", "test"):
        split_dir = outputs_dir / split
        if not split_dir.exists():
            continue
        for path in split_dir.glob("*.jsonl"):
            for row in _load_jsonl(path):
                text = row.get("noisy_text", "")
                if not text:
                    continue
                checked += 1
                if not is_lossless(text):
                    bad.append((path.name, row.get("source_id"), "not lossless"))
                    continue
                bad_clusters = [c for c in clusters(text) if starts_with_combining(c)]
                if not bad_clusters:
                    continue
                original = row.get("original_text", "")
                inherited = {c for c in clusters(original) if starts_with_combining(c)} if original else set()
                new_bad = [c for c in bad_clusters if c not in inherited]
                if new_bad:
                    bad.append((path.name, row.get("source_id"), f"{len(new_bad)} new combining-start clusters"))

    if checked == 0:
        _notes["grapheme_integrity"] = "vacuous: data/outputs/ has no generated files yet"
        return True
    ok = not bad
    if not ok:
        _notes["grapheme_integrity"] = f"{len(bad)}/{checked} rows failed grapheme integrity, e.g. {bad[:5]}"
    return ok


def check_codemix_substitution_spec() -> bool:
    """codemix v2's real design spec, checked independently of trusting
    src.noisers.codemix's own correctness: for every persisted codemix
    output row, recompute the eligible-word-type pool straight from the
    frozen word bank + original_text (reusing the noiser's own wordbank
    loader and src.graphemes.text_runs, but NOT calling apply()/_apply() —
    this must independently re-derive the pool, not just re-run the same
    selection code and trivially agree with it), and assert:
      1. n_substitutions == min(k, pool_size), where k is 1 (light) or 2
         (heavy) and pool_size prefers plausible-flagged types, falling
         back to all eligible types only when none are plausible — the
         exact "prefer plausible, fall back to eligible, cap at k" contract
         from the module docstring's "honest tradeoff" section.
      2. A post with pool_size == 0 is byte-identical to its source
         (noisy_text == original_text) — forced selection must never
         invent a substitution where nothing is eligible.
    This is the primary correctness gate for the v2 redesign — the whole
    point of the redesign was fixing v1's 85.8%/79.7% untouched-row rate,
    so the invariant checks the SPEC that fixes it, not a calibrated rate
    number (see TARGET_NOISE_RATE's docstring in src/noisers/codemix.py for
    why that's demoted to a drift tripwire instead)."""
    from src.graphemes import text_runs as _text_runs
    from src.noisers.codemix import _WORDS_PER_POST, _load_wordbank

    outputs_dir = REPO_ROOT / "data" / "outputs"
    codemix_files = []
    for split in ("train", "test"):
        split_dir = outputs_dir / split
        if split_dir.exists():
            codemix_files.extend(sorted(split_dir.glob("codemix_*.jsonl")))

    if not codemix_files:
        _notes["codemix_substitution_spec"] = "vacuous: no data/outputs/*/codemix_*.jsonl yet"
        return True

    wordbank = _load_wordbank()
    if not wordbank:
        _notes["codemix_substitution_spec"] = "vacuous: data/lexicon/codemix_wordbank.jsonl not yet built"
        return True

    checked = 0
    bad = []
    for path in codemix_files:
        severity = "heavy" if "heavy" in path.stem else "light"
        k = _WORDS_PER_POST[severity]
        for row in _load_jsonl(path):
            checked += 1
            sinhala_words = {run for is_sinhala, run in _text_runs(row["original_text"]) if is_sinhala}
            eligible = sinhala_words & wordbank.keys()
            plausible = {w for w in eligible if wordbank[w]["codemix_plausible"]}
            pool_size = len(plausible) if plausible else len(eligible)
            expected_n = min(k, pool_size)
            actual_n = row.get("n_substitutions", -1)
            if actual_n != expected_n:
                bad.append((path.name, row["source_id"], f"n_substitutions={actual_n}, expected {expected_n}"))
            elif pool_size == 0 and row["noisy_text"] != row["original_text"]:
                bad.append((path.name, row["source_id"], "pool_size=0 but noisy_text != original_text"))
            if len(bad) > 20:
                break
        if len(bad) > 20:
            break

    ok = not bad
    if not ok:
        _notes["codemix_substitution_spec"] = f"{len(bad)}(+)/{checked} rows violate the substitution spec, e.g. {bad[:5]}"
    return ok


def check_misspell_substitution_spec() -> bool:
    """src.noisers.misspell's real design spec, checked independently of
    trusting the noiser's own correctness — same discipline as
    check_codemix_substitution_spec: recompute structure from
    (original_text, noisy_text) and the FROZEN lexicon files, never by
    re-running apply()'s own rng-driven selection.

    Tokenizes both original_text and noisy_text into (kind, token) pairs
    using the same static, non-random word-boundary rule apply() uses
    (a Sinhala grapheme-cluster run is one token; each Latin alpha
    substring inside a non-Sinhala run is its own token) — this rule is
    structural, not a selection decision, so reusing it here doesn't
    trivially agree with the noiser's choices. For every token that
    changed, asserts:
      - word count and token kind sequence are unchanged (neither channel
        adds, drops, or reorders words);
      - for a Sinhala token: EXACTLY ONE grapheme cluster differs, cluster
        COUNT is unchanged, the new cluster is not a fresh ZWJ/ZWNJ
        introduction, and the new cluster is an actual member of the old
        cluster's confusion set in data/lexicon/misspell_confusions.jsonl
        (Channel A must never invent a substitution outside its frozen,
        human-reviewed lexicon);
      - for a Latin token: the new form is not one of
        data/lexicon/word_variants.jsonl's attested romanizations (Channel
        B's orthogonality rule against overlapping with transliteration's
        severity lever — see src/noisers/misspell.py's module docstring).
    Finally, recomputes realised_noise_rate from the token diff and checks
    it matches the persisted row's value — catching any drift between what
    the row claims and what the text actually shows.
    """
    from src.graphemes import clusters as _clusters, text_runs as _text_runs, ZWJ, ZWNJ
    from src.noisers.misspell import _LATIN_WORD_RE, _load_confusions, _load_word_variants_latin

    outputs_dir = REPO_ROOT / "data" / "outputs"
    misspell_files = []
    for split in ("train", "test"):
        split_dir = outputs_dir / split
        if split_dir.exists():
            misspell_files.extend(sorted(split_dir.glob("misspell_*.jsonl")))

    if not misspell_files:
        _notes["misspell_substitution_spec"] = "vacuous: no data/outputs/*/misspell_*.jsonl yet"
        return True

    confusions = _load_confusions()
    if not confusions:
        _notes["misspell_substitution_spec"] = "vacuous: data/lexicon/misspell_confusions.jsonl not yet built"
        return True
    excluded_latin = _load_word_variants_latin()

    def _tokenize(text: str) -> list[tuple[str, str]]:
        tokens = []
        for is_sinhala, run in _text_runs(text):
            if is_sinhala:
                tokens.append(("sinhala", run))
            else:
                for m in _LATIN_WORD_RE.finditer(run):
                    tokens.append(("latin", m.group(0)))
        return tokens

    RATE_TOLERANCE = 1e-6
    checked = 0
    bad = []
    for path in misspell_files:
        for row in _load_jsonl(path):
            checked += 1
            orig_tokens = _tokenize(row["original_text"])
            noisy_tokens = _tokenize(row["noisy_text"])
            if len(orig_tokens) != len(noisy_tokens):
                bad.append((path.name, row["source_id"], "word count changed"))
                continue

            n_altered = 0
            row_bad = False
            for (kind_o, tok_o), (kind_n, tok_n) in zip(orig_tokens, noisy_tokens):
                if kind_o != kind_n:
                    bad.append((path.name, row["source_id"], "token kind mismatch"))
                    row_bad = True
                    break
                if tok_o == tok_n:
                    continue
                n_altered += 1
                if kind_o == "sinhala":
                    cs_o, cs_n = _clusters(tok_o), _clusters(tok_n)
                    if len(cs_o) != len(cs_n):
                        bad.append((path.name, row["source_id"], f"cluster count changed: {tok_o!r}->{tok_n!r}"))
                        row_bad = True
                        break
                    diffs = [(a, b) for a, b in zip(cs_o, cs_n) if a != b]
                    if len(diffs) != 1:
                        bad.append((path.name, row["source_id"],
                                     f"expected exactly 1 changed cluster, got {len(diffs)}: {tok_o!r}->{tok_n!r}"))
                        row_bad = True
                        break
                    old_c, new_c = diffs[0]
                    if ZWJ in new_c or ZWNJ in new_c:
                        bad.append((path.name, row["source_id"], f"ZWJ/ZWNJ introduced: {new_c!r}"))
                        row_bad = True
                        break
                    if new_c not in confusions.get(old_c, []):
                        bad.append((path.name, row["source_id"],
                                     f"{new_c!r} not a member of {old_c!r}'s confusion set"))
                        row_bad = True
                        break
                else:  # latin
                    if tok_n in excluded_latin:
                        bad.append((path.name, row["source_id"],
                                     f"Channel B produced an attested transliteration variant: {tok_n!r}"))
                        row_bad = True
                        break
            if row_bad:
                continue

            n_words = len(orig_tokens)
            expected_rate = (n_altered / n_words) if n_words else 0.0
            actual_rate = row.get("realised_noise_rate", -1)
            if abs(actual_rate - expected_rate) > RATE_TOLERANCE:
                bad.append((path.name, row["source_id"],
                             f"realised_noise_rate={actual_rate}, recomputed {expected_rate}"))

            if len(bad) > 20:
                break
        if len(bad) > 20:
            break

    ok = not bad
    if not ok:
        _notes["misspell_substitution_spec"] = f"{len(bad)}(+)/{checked} rows violate the substitution spec, e.g. {bad[:5]}"
    return ok


def check_abbreviate_substitution_spec() -> bool:
    """src.noisers.abbreviate's forced-per-post design spec, checked
    independently of trusting the noiser's own selection logic — same
    discipline and same rigor level as check_codemix_substitution_spec
    (which this deliberately mirrors: recompute the eligible pool from
    scratch and check spec-compliance, not byte-for-byte reconstruct which
    exact occurrences were chosen, since WHICH ones get picked is legitimately
    rng's job and not independently re-derivable without re-running the
    noiser's own draw).

    Reuses the noiser's own PURE, non-random helper functions
    (`_find_occurrences`, `_non_overlapping`) to recompute the eligible,
    non-overlapping bigram-occurrence pool straight from original_text and
    the frozen lexicon — but never calls `_apply()`/`apply()`, which involve
    the rng draw this check must not simply agree with by construction.
    Asserts:
      1. `n_substitutions == min(k, pool_size)`, where k is 1 (light) or 2
         (heavy) — forced-per-post selection must always take exactly this
         many, never fewer just because a draw "chose" fewer.
      2. A post with `pool_size == 0` is byte-identical to its source
         (`noisy_text == original_text`) — forced selection must never
         invent a substitution where nothing is eligible.
    """
    from src.graphemes import text_runs as _text_runs
    from src.noisers.abbreviate import _BIGRAMS_PER_POST, _find_occurrences, _non_overlapping, _load_lexicon

    outputs_dir = REPO_ROOT / "data" / "outputs"
    abbreviate_files = []
    for split in ("train", "test"):
        split_dir = outputs_dir / split
        if split_dir.exists():
            abbreviate_files.extend(sorted(split_dir.glob("abbreviate_*.jsonl")))

    if not abbreviate_files:
        _notes["abbreviate_substitution_spec"] = "vacuous: no data/outputs/*/abbreviate_*.jsonl yet"
        return True

    lexicon = _load_lexicon()
    if not lexicon:
        _notes["abbreviate_substitution_spec"] = "vacuous: data/lexicon/abbreviate_initialisms.jsonl not yet built"
        return True

    checked = 0
    bad = []
    for path in abbreviate_files:
        severity = "heavy" if "heavy" in path.stem else "light"
        k = _BIGRAMS_PER_POST[severity]
        for row in _load_jsonl(path):
            checked += 1
            runs = _text_runs(row["original_text"])
            pool = _non_overlapping(_find_occurrences(runs, lexicon))
            pool_size = len(pool)
            expected_n = min(k, pool_size)
            actual_n = row.get("n_substitutions", -1)
            if actual_n != expected_n:
                bad.append((path.name, row["source_id"], f"n_substitutions={actual_n}, expected {expected_n}"))
            elif pool_size == 0 and row["noisy_text"] != row["original_text"]:
                bad.append((path.name, row["source_id"], "pool_size=0 but noisy_text != original_text"))
            if len(bad) > 20:
                break
        if len(bad) > 20:
            break

    ok = not bad
    if not ok:
        _notes["abbreviate_substitution_spec"] = f"{len(bad)}(+)/{checked} rows violate the substitution spec, e.g. {bad[:5]}"
    return ok


def check_split_isolation() -> bool:
    """No source_id may appear in both train and test NOISED outputs, and
    every row's own `split` field must match the directory it's written
    under. Vacuous until data/outputs/ has any generated files."""
    outputs_dir = REPO_ROOT / "data" / "outputs"
    ids_by_split: dict[str, set[str]] = {"train": set(), "test": set()}
    mismatched = []
    n_files = 0
    for split in ("train", "test"):
        split_dir = outputs_dir / split
        if not split_dir.exists():
            continue
        for path in split_dir.glob("*.jsonl"):
            n_files += 1
            for row in _load_jsonl(path):
                ids_by_split[split].add(row["source_id"])
                if row.get("split") != split:
                    mismatched.append((str(path), row["source_id"]))

    if n_files == 0:
        _notes["split_isolation"] = "vacuous: data/outputs/ has no generated files yet"
        return True

    overlap = ids_by_split["train"] & ids_by_split["test"]
    ok = not overlap and not mismatched
    if not ok:
        reasons = []
        if overlap:
            reasons.append(f"{len(overlap)} source_ids appear in both train and test outputs")
        if mismatched:
            reasons.append(f"{len(mismatched)} rows have a split field mismatching their directory")
        _notes["split_isolation"] = "; ".join(reasons)
    return ok


def run_invariants() -> dict[str, bool]:
    """Return {check_name: pass|fail}. See invariant_notes() for context."""
    _notes.clear()
    checks = {
        "gold_sets_present": check_gold_sets_present,
        "reference_corpus_present": check_reference_corpus_present,
        "gold_reference_disjoint": check_gold_reference_disjoint,
        "gold_romanized_side_has_no_sinhala": check_gold_romanized_side_has_no_sinhala,
        "gold_sinhala_side_has_sinhala": check_gold_sinhala_side_has_sinhala,
        "grapheme_roundtrip_lossless": check_grapheme_roundtrip_lossless,
        "sold_counts_match_paper": check_sold_counts_match_paper,
        "sold_split_disjoint": check_sold_split_disjoint,
        "schema_validates": check_schema_validates,
        "no_empty_outputs": check_no_empty_outputs,
        "determinism": check_determinism,
        "grapheme_integrity": check_grapheme_integrity,
        "codemix_substitution_spec": check_codemix_substitution_spec,
        "misspell_substitution_spec": check_misspell_substitution_spec,
        "abbreviate_substitution_spec": check_abbreviate_substitution_spec,
        "split_isolation": check_split_isolation,
    }
    return {name: fn() for name, fn in checks.items()}


def invariant_notes() -> dict[str, str]:
    """Context for any check in the last run_invariants() call that needs
    more than pass/fail — in particular, every vacuous pass is noted here so
    it never reads as a silent green check."""
    return dict(_notes)
