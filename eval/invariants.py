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

    from eval.gold_cer import discover_backends

    backends = discover_backends()
    if not backends:
        _notes["determinism"] = "vacuous: no romanizer backend available yet"
        return True
    sample = [row["sinhala"] for row in words[:50]]
    for name, fn in backends.items():
        run1 = [fn(s) for s in sample]
        run2 = [fn(s) for s in sample]
        if run1 != run2:
            bad.append(name)

    import importlib

    noiser_sample = [row["sinhala"] for row in words[:20]]
    for noiser_name in ("transliteration", "codemix"):
        try:
            module = importlib.import_module(f"src.noisers.{noiser_name}")
        except ImportError:
            continue
        for severity in getattr(module, "TARGET_NOISE_RATE", {}):
            run1 = [module.apply(t, severity, seed=1337) for t in noiser_sample]
            run2 = [module.apply(t, severity, seed=1337) for t in noiser_sample]
            if run1 != run2:
                bad.append(f"{noiser_name}/{severity}")

    ok = not bad
    if not ok:
        _notes["determinism"] = f"non-deterministic backends/noisers: {bad}"
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
    """codemix round 5's real design spec (budget-capped, distribution-
    sampled CMI), checked independently of trusting src.noisers.codemix's
    own correctness: for every persisted codemix output row, recompute the
    MAXIMAL non-overlapping unit set straight from original_text via
    src.noisers.codemix._find_max_units — a PURE function with no
    severity/budget/rng dependency, so calling it here is re-deriving
    structure, not re-running the RNG-driven selection and trivially
    agreeing with it (same discipline the pre-round-5 version of this check
    used for the word-only pool). Then assert the packing contract
    _pack_units_to_budget implements:
      1. n_substitutions present, target_cmi present and within [0, 100].
      2. n_substitutions == 0  <=>  noisy_text == original_text — forced
         selection must never invent a substitution from nothing, and
         conversely a chosen unit must always show up in the output.
      3. Let max_tokens = sum of n_words over every unit in the maximal set,
         and implied_budget = round(target_cmi/100 * n_sinhala_words).
         If max_tokens <= implied_budget: the full ceiling was necessarily
         used, so n_substitutions must equal len(maximal_units) exactly
         (nothing left on the table when the budget covers everything).
         Otherwise: n_substitutions must be <= len(maximal_units) (can never
         choose more units than exist) — this is the bound side of the
         packing contract; it cannot also assert an exact count here
         because _pack_units_to_budget's rng-seeded packing is legitimately
         one of several budget-satisfying subsets, and re-deriving THAT
         exact subset without calling the RNG-driven code would mean
         reimplementing _pack_units_to_budget's own randomised bin-packing
         a second time — precisely the "second copy that could drift"
         situation this discipline exists to avoid.
    """
    from src.noisers.codemix import _find_max_units, _load_cmi_bands

    outputs_dir = REPO_ROOT / "data" / "outputs"
    codemix_files = []
    for split in ("train", "test"):
        split_dir = outputs_dir / split
        if split_dir.exists():
            codemix_files.extend(sorted(split_dir.glob("codemix_*.jsonl")))

    if not codemix_files:
        _notes["codemix_substitution_spec"] = "vacuous: no data/outputs/*/codemix_*.jsonl yet"
        return True

    try:
        _load_cmi_bands()
    except FileNotFoundError:
        _notes["codemix_substitution_spec"] = "vacuous: data/lexicon/codemix_cmi_bands.json not yet built"
        return True

    checked = 0
    bad = []
    for path in codemix_files:
        for row in _load_jsonl(path):
            checked += 1
            source_id = row["source_id"]
            target_cmi = row.get("target_cmi")
            actual_n = row.get("n_substitutions", -1)
            if target_cmi is None or not (0.0 <= target_cmi <= 100.0):
                bad.append((path.name, source_id, f"target_cmi={target_cmi!r} out of [0,100]"))
                continue

            runs, units = _find_max_units(row["original_text"])
            n_sinhala_words = sum(1 for is_sinhala, _run in runs if is_sinhala)
            max_tokens = sum(u["n_words"] for u in units)
            implied_budget = round(target_cmi / 100 * n_sinhala_words) if n_sinhala_words else 0

            is_changed = row["noisy_text"] != row["original_text"]
            if actual_n == 0 and is_changed:
                bad.append((path.name, source_id, "n_substitutions=0 but noisy_text != original_text"))
            elif actual_n > 0 and not is_changed:
                bad.append((path.name, source_id, f"n_substitutions={actual_n} but noisy_text == original_text"))
            elif max_tokens <= implied_budget and actual_n != len(units):
                bad.append((path.name, source_id,
                            f"n_substitutions={actual_n}, expected {len(units)} (budget covers full ceiling)"))
            elif actual_n > len(units):
                bad.append((path.name, source_id,
                            f"n_substitutions={actual_n} exceeds max achievable units={len(units)}"))
            elif target_cmi > 0 and units and actual_n == 0:
                bad.append((path.name, source_id,
                            f"target_cmi={target_cmi:.2f} > 0 with {len(units)} eligible unit(s) "
                            "but n_substitutions=0 -- budget=0-but-target>0 fallback did not fire"))
            if len(bad) > 20:
                break
        if len(bad) > 20:
            break

    ok = not bad
    if not ok:
        _notes["codemix_substitution_spec"] = f"{len(bad)}(+)/{checked} rows violate the substitution spec, e.g. {bad[:5]}"
    return ok


def check_codemix_cmi_distribution() -> bool:
    """Does what actually got generated match the declared target?
    Recomputes realised CMI over every persisted codemix row using
    eval.cmi's SCRIPT-ONLY classifier (script_only=True — not the natural-
    text LID filter, which specifically undercounts this project's own
    generated vocabulary; see eval/cmi.py's token_sequence_script_only
    docstring), and asserts the realised mean CMI per severity is within a
    generous +/-5 point tolerance of that severity's frozen band-implied
    mean (data/lexicon/codemix_cmi_bands.json)."""
    from src.noisers.codemix import _load_cmi_bands
    from eval import cmi as cmi_mod

    if not cmi_mod.is_available():
        _notes["codemix_cmi_distribution"] = f"vacuous: eval.cmi unavailable ({cmi_mod.unavailable_reason()})"
        return True

    outputs_dir = REPO_ROOT / "data" / "outputs"
    codemix_files = []
    for split in ("train", "test"):
        split_dir = outputs_dir / split
        if split_dir.exists():
            codemix_files.extend(sorted(split_dir.glob("codemix_*.jsonl")))
    if not codemix_files:
        _notes["codemix_cmi_distribution"] = "vacuous: no data/outputs/*/codemix_*.jsonl yet"
        return True

    try:
        bands = _load_cmi_bands()
    except FileNotFoundError:
        _notes["codemix_cmi_distribution"] = "vacuous: data/lexicon/codemix_cmi_bands.json not yet built"
        return True

    def _band_implied_mean(severity: str) -> float:
        total_w = sum(b[2] for b in bands[severity])
        return sum(((b[0] + b[1]) / 2) * b[2] for b in bands[severity]) / total_w

    TOLERANCE = 5.0
    bad = []
    detail: dict[str, dict] = {}
    for path in codemix_files:
        severity = "heavy" if "heavy" in path.stem else "light"
        rows = _load_jsonl(path)
        texts = [row["noisy_text"] for row in rows]
        stats = cmi_mod.corpus_cmi_stats(texts, script_only=True, only_mixed=False)
        realised_mean = stats["cmi_mean"] if stats["cmi_mean"] is not None else 0.0
        expected_mean = _band_implied_mean(severity)
        diff = abs(realised_mean - expected_mean)
        detail[path.stem] = {"realised_mean": round(realised_mean, 2), "expected_mean": round(expected_mean, 2)}
        if diff > TOLERANCE:
            bad.append((path.name, f"realised_mean={realised_mean:.2f}, expected={expected_mean:.2f}, "
                                    f"diff={diff:.2f} > {TOLERANCE}"))
    _notes["codemix_cmi_distribution_detail"] = json.dumps(detail, ensure_ascii=False)

    ok = not bad
    if not ok:
        _notes["codemix_cmi_distribution"] = f"{len(bad)} file(s) drifted from their declared CMI target: {bad}"
    return ok


def check_codemix_no_affect_substitution() -> bool:
    """No entry in the CURRENT frozen word bank or phrase bank may have an
    English side that is an evaluative/abusive/slur headword — checked
    structurally against the frozen files themselves, not generated output,
    so it catches a regression even before anything is generated from it."""
    from src.noisers.codemix import LEXICON_PATH, PHRASEBANK_PATH

    abusive_headwords = {
        "maniac", "crazy", "idiot", "fool", "stupid", "dog", "pig", "devil",
        "demon", "traitor", "thief", "liar", "shit", "moron", "beast", "swine",
        "bastard", "whore", "bitch", "rascal", "wretch", "filth", "madman",
        "lunatic",
    }

    if not LEXICON_PATH.exists():
        _notes["codemix_no_affect_substitution"] = "vacuous: data/lexicon/codemix_wordbank.jsonl not yet built"
        return True

    bad = []
    for row in _load_jsonl(LEXICON_PATH):
        english = row.get("english", "")
        headword = english.split()[0].lower().strip(".,") if english else ""
        if headword in abusive_headwords:
            bad.append(("wordbank", row["sinhala"], english))
        if len(bad) > 20:
            break

    if len(bad) <= 20 and PHRASEBANK_PATH.exists():
        for row in _load_jsonl(PHRASEBANK_PATH):
            if not row.get("codemix_plausible"):
                continue
            english = row.get("english", "")
            words = {w.lower().strip(".,") for w in english.split()}
            if words & abusive_headwords:
                bad.append(("phrasebank", row["sinhala"], english))
            if len(bad) > 20:
                break

    ok = not bad
    if not ok:
        _notes["codemix_no_affect_substitution"] = (
            f"{len(bad)}(+) affect-bearing entries present, e.g. {bad[:5]} "
            "— check data/lexicon/codemix_review_corrections.jsonl or codemix_phrase_"
            "review_corrections.jsonl for a missing or overwritten removal row"
        )
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
        "codemix_cmi_distribution": check_codemix_cmi_distribution,
        "codemix_no_affect_substitution": check_codemix_no_affect_substitution,
        "split_isolation": check_split_isolation,
    }
    return {name: fn() for name, fn in checks.items()}


def invariant_notes() -> dict[str, str]:
    """Context for any check in the last run_invariants() call that needs
    more than pass/fail — in particular, every vacuous pass is noted here so
    it never reads as a silent green check."""
    return dict(_notes)
