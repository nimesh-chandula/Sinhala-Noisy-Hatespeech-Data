"""
Eval harness — the single source of truth for whether a change is an improvement.

Run:  python eval/harness.py               (always exits 0 in Phase 0)
      python eval/harness.py --strict       (exits 1 if any invariant/regression fails)

Produces eval/report.json and eval/report.md per the evaluation contract:
    invariants, gold_cer, realism_jsd, regression, noise_rate_error, summary
plus additive keys (gold_cer_detail, realism_detail, invariants_notes, meta,
targets, status) that carry extra detail without breaking the contract shape
later phases depend on. Empty sections render as "no_candidate" /
"not_applicable" — this must always run to completion, never crash, even
before any romanizer or noiser exists.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
EVAL_DIR = Path(__file__).resolve().parent
if str(EVAL_DIR) not in sys.path:
    sys.path.insert(0, str(EVAL_DIR))

from invariants import run_invariants, invariant_notes          # noqa: E402
from gold_cer import (                                           # noqa: E402
    run_gold_cer,
    run_gold_cer_detail,
    run_gold_cer_backends_unavailable,
    cer,
)
from realism import run_realism, realism_not_applicable, load_reference, baseline_jsd, NORMALIZE_VERSION  # noqa: E402
from src.schema import Row                                       # noqa: E402

REPORT_JSON = EVAL_DIR / "report.json"
REPORT_MD = EVAL_DIR / "report.md"
REGRESSION_DIR = EVAL_DIR / "regression"

# Project targets — used only to annotate the report, not to gate here.
NOISE_RATE_TOLERANCE = 0.05
GOLD_CER_TARGET = 0.10

NO_CANDIDATE = "no_candidate"
NOT_APPLICABLE = "not_applicable"


# ---------------------------------------------------------------------------
# Regression runner
# ---------------------------------------------------------------------------

def _run_cer_case(case: dict) -> tuple[bool, str]:
    got = cer(case["hypothesis"], case["reference"])
    tol = case.get("tolerance", 1e-9)
    ok = abs(got - case["expected_cer"]) <= tol
    return ok, f"got={got}"


def _run_jsd_case(case: dict) -> tuple[bool, str]:
    from realism import jensen_shannon, _dist, normalize_v2

    dist_a = _dist([normalize_v2(t) for t in case["texts_a"]])
    dist_b = _dist([normalize_v2(t) for t in case["texts_b"]])
    got = jensen_shannon(dist_a, dist_b)
    tol = case.get("tolerance", 1e-9)
    ok = abs(got - case["expected_jsd"]) <= tol
    return ok, f"got={got}"


def _run_graphemes_case(case: dict) -> tuple[bool, str]:
    from src.graphemes import clusters, is_lossless, starts_with_combining

    got = clusters(case["text"])
    reasons = []
    ok = True
    if got != case["expected_clusters"]:
        ok = False
        reasons.append(f"clusters={got!r} != expected={case['expected_clusters']!r}")
    if case.get("assert_lossless") and not is_lossless(case["text"]):
        ok = False
        reasons.append("round-trip not lossless")
    if case.get("assert_no_combining_start"):
        bad = [c for c in got if starts_with_combining(c)]
        if bad:
            ok = False
            reasons.append(f"clusters starting with a combining mark: {bad!r}")
    return ok, "; ".join(reasons) if reasons else "ok"


def _run_schema_case(case: dict) -> tuple[bool, str]:
    row = Row(**case["row"])
    try:
        row.validate()
        raised = False
    except AssertionError:
        raised = True
    expect_raise = case["expect"] == "raises"
    ok = raised == expect_raise
    return ok, f"raised={raised}, expected={case['expect']}"


def _run_noiser_case(case: dict) -> tuple[bool, str]:
    """Frozen hand-checked noiser output: apply(text, severity, seed) must
    equal an exact expected string, AND running it twice must be identical
    (determinism, per CLAUDE.md golden rule 4) — the same discipline as
    check_determinism in invariants.py, but pinned to specific known input."""
    import importlib

    module = importlib.import_module(f"src.noisers.{case['noiser']}")
    got_text, got_rate = module.apply(case["text"], case["severity"], case["seed"])
    replay_text, _ = module.apply(case["text"], case["severity"], case["seed"])
    reasons = []
    ok = True
    if got_text != case["expected_text"]:
        ok = False
        reasons.append(f"text={got_text!r} != expected={case['expected_text']!r}")
    if got_text != replay_text:
        ok = False
        reasons.append("non-deterministic: two calls with the same (text, severity, seed) differed")
    tol = case.get("tolerance", 1e-9)
    if abs(got_rate - case["expected_rate"]) > tol:
        ok = False
        reasons.append(f"rate={got_rate} != expected={case['expected_rate']}")
    return ok, "; ".join(reasons) if reasons else "ok"


_CASE_RUNNERS = {
    "cer": _run_cer_case,
    "jsd": _run_jsd_case,
    "graphemes": _run_graphemes_case,
    "schema": _run_schema_case,
    "noiser": _run_noiser_case,
}

# {condition: {severity: target_rate}} for every noiser that's actually
# implemented — read from the noiser module itself so the target lives in
# exactly one place. Extend as Phase 3/4 noisers come online.
#
# _NOISERS_UNAVAILABLE records anything that failed to import so it can be
# surfaced in the report instead of silently vanishing — a bare
# `except ImportError: pass` here once let a whole interpreter's missing
# `aksharamukha` package erase transliteration from noise_rate_error without
# any trace in a "PASS" report. See LOG.md Stage 0 / gold_cer.py's
# discover_backends_with_status() for the matching fix on the romanizer side.
_NOISER_TARGETS = {}
_NOISERS_UNAVAILABLE: dict[str, str] = {}
try:
    from src.noisers import transliteration as _transliteration_noiser

    _NOISER_TARGETS["transliteration"] = _transliteration_noiser.TARGET_NOISE_RATE
except ImportError as _e:
    _NOISERS_UNAVAILABLE["transliteration"] = str(_e)
try:
    from src.noisers import codemix as _codemix_noiser

    _NOISER_TARGETS["codemix"] = _codemix_noiser.TARGET_NOISE_RATE
except ImportError as _e:
    _NOISERS_UNAVAILABLE["codemix"] = str(_e)
try:
    from src.noisers import misspell as _misspell_noiser

    if getattr(_misspell_noiser, "TARGET_NOISE_RATE", None):
        _NOISER_TARGETS["misspell"] = _misspell_noiser.TARGET_NOISE_RATE
except ImportError as _e:
    _NOISERS_UNAVAILABLE["misspell"] = str(_e)
try:
    from src.noisers import abbreviate as _abbreviate_noiser

    _NOISER_TARGETS["abbreviate"] = _abbreviate_noiser.TARGET_NOISE_RATE
except ImportError as _e:
    _NOISERS_UNAVAILABLE["abbreviate"] = str(_e)


def compute_noise_rate_error() -> dict[str, float]:
    """{condition_severity: |mean realised_noise_rate - target|}, read from
    data/outputs/{split}/{condition}_{severity}.jsonl. Empty until a noiser
    has both a TARGET_NOISE_RATE and generated output to check it against."""
    outputs_dir = REPO_ROOT / "data" / "outputs"
    errors: dict[str, float] = {}
    for condition, targets in _NOISER_TARGETS.items():
        for severity, target in targets.items():
            rates = []
            for split in ("train", "test"):
                path = outputs_dir / split / f"{condition}_{severity}.jsonl"
                if not path.exists():
                    continue
                with path.open(encoding="utf-8") as f:
                    rates.extend(json.loads(line)["realised_noise_rate"] for line in f if line.strip())
            if rates:
                mean_rate = sum(rates) / len(rates)
                errors[f"{condition}_{severity}"] = abs(mean_rate - target)
    return errors


def load_regression_cases() -> dict[str, bool]:
    """Run every frozen hand-checked case in eval/regression/*.json.
    Returns {case_id: pass|fail}. Missing directory -> {} (harness still runs)."""
    if not REGRESSION_DIR.exists():
        return {}
    results = {}
    for path in sorted(REGRESSION_DIR.glob("*.json")):
        case = json.loads(path.read_text(encoding="utf-8"))
        case_id = case.get("id", path.stem)
        runner = _CASE_RUNNERS.get(case["kind"])
        if runner is None:
            results[case_id] = False
            continue
        try:
            ok, _detail = runner(case)
        except Exception:
            ok = False
        results[case_id] = ok
    return results


# ---------------------------------------------------------------------------
# Report assembly
# ---------------------------------------------------------------------------

def build_summary(invariants, gold_cer, realism, regression, noise_rate_error, backends_unavailable) -> str:
    inv_ok = all(invariants.values()) if invariants else True
    reg_ok = all(regression.values()) if regression else True
    best_cer = min(gold_cer.values()) if gold_cer else None
    parts = [
        f"invariants={'PASS' if inv_ok else 'FAIL'}",
        f"regression={'PASS' if reg_ok else 'FAIL'} ({sum(regression.values())}/{len(regression)})"
        if regression else "regression=n/a",
        f"best_gold_cer={round(best_cer, 4) if best_cer is not None else NO_CANDIDATE}"
        f" (target<{GOLD_CER_TARGET})",
        f"realism_jsd={ {k: round(v, 4) for k, v in realism.items()} if realism else NO_CANDIDATE }",
        f"noise_rate_error={noise_rate_error if noise_rate_error else NOT_APPLICABLE}",
    ]
    # Loud on purpose: a report must never say PASS while quietly missing a
    # backend/noiser this interpreter couldn't import. See _NOISERS_UNAVAILABLE
    # and gold_cer.discover_backends_with_status().
    all_unavailable = {**backends_unavailable.get("romanizer_backends", {}), **backends_unavailable.get("noisers", {})}
    if all_unavailable:
        parts.append(f"WARNING backends_unavailable={sorted(all_unavailable)}")
    return " | ".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict", action="store_true",
        help="exit 1 if any invariant or regression case fails (for CI use from Phase 1 on)",
    )
    args = parser.parse_args()

    invariants = run_invariants()
    inv_notes = invariant_notes()
    gold_cer_detail = run_gold_cer_detail()
    gold_cer_primary = run_gold_cer()
    romanizer_backends_unavailable = run_gold_cer_backends_unavailable()
    realism = run_realism()
    realism_na = realism_not_applicable()
    regression = load_regression_cases()
    noise_rate_error = compute_noise_rate_error()
    backends_unavailable = {
        "romanizer_backends": romanizer_backends_unavailable,
        "noisers": _NOISERS_UNAVAILABLE,
    }

    reference = load_reference()
    realism_floor = baseline_jsd(reference) if reference else None

    report = {
        "invariants": invariants,
        "invariants_notes": inv_notes,
        "gold_cer": gold_cer_primary if gold_cer_primary else NO_CANDIDATE,
        "gold_cer_detail": gold_cer_detail if gold_cer_detail else NO_CANDIDATE,
        "realism_jsd": realism if realism else NO_CANDIDATE,
        "realism_not_applicable": realism_na if realism_na else {},
        "realism_baseline_jsd": realism_floor if realism_floor is not None else NOT_APPLICABLE,
        "regression": regression if regression else NO_CANDIDATE,
        "noise_rate_error": noise_rate_error if noise_rate_error else NOT_APPLICABLE,
        "backends_unavailable": backends_unavailable,
        "targets": {
            "gold_cer_primary_metric": "word_multi_min",
            "gold_cer": GOLD_CER_TARGET,
            "noise_rate_tolerance": NOISE_RATE_TOLERANCE,
            "realism_reduction_from_baseline": 0.30,
        },
        "meta": {
            "realism_normalize_version": NORMALIZE_VERSION,
        },
        "summary": build_summary(
            invariants, gold_cer_primary, realism, regression, noise_rate_error, backends_unavailable
        ),
    }

    inv_ok = all(invariants.values()) if invariants else True
    reg_ok = all(regression.values()) if regression else True
    report["status"] = "PASS" if (inv_ok and reg_ok) else "FAIL"

    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_md(report)
    print(report["summary"])

    if args.strict and report["status"] != "PASS":
        sys.exit(1)


def _write_md(report: dict) -> None:
    lines = ["# Eval report", "", f"**{report['summary']}**", ""]

    unavailable = report.get("backends_unavailable", {})
    all_unavailable = {**unavailable.get("romanizer_backends", {}), **unavailable.get("noisers", {})}
    if all_unavailable:
        lines.append("## ⚠️ backends_unavailable (this interpreter)")
        lines.append(
            "Every metric below was computed WITHOUT these — re-run with the "
            "interpreter that has them installed before trusting `best_gold_cer` "
            "or `noise_rate_error` as final numbers."
        )
        for name, reason in unavailable.get("romanizer_backends", {}).items():
            lines.append(f"- romanizer backend `{name}`: {reason}")
        for name, reason in unavailable.get("noisers", {}).items():
            lines.append(f"- noiser `{name}`: {reason}")
        lines.append("")

    lines.append("## invariants")
    for k, v in report["invariants"].items():
        note = f" — _{report['invariants_notes'][k]}_" if k in report["invariants_notes"] else ""
        lines.append(f"- `{k}`: {'PASS' if v else 'FAIL'}{note}")
    lines.append("")

    lines.append("## gold_cer (primary metric: word_multi_min)")
    if report["gold_cer"] == NO_CANDIDATE:
        lines.append("_no_candidate — no romanizer backend registered yet_")
    else:
        for backend, detail in report["gold_cer_detail"].items():
            lines.append(f"- `{backend}`:")
            for metric, val in detail.items():
                lines.append(f"    - {metric}: {round(val, 4) if val is not None else 'n/a'}")
    lines.append("")

    lines.append("## realism_jsd")
    lines.append(f"- baseline floor (reference vs itself, split-half): "
                  f"{round(report['realism_baseline_jsd'], 4) if isinstance(report['realism_baseline_jsd'], float) else report['realism_baseline_jsd']}")
    if report["realism_jsd"] == NO_CANDIDATE:
        lines.append("_no_candidate — no noised condition generated yet_")
    else:
        for k, v in report["realism_jsd"].items():
            lines.append(f"- `{k}`: {round(v, 4)}")
    for k, reason in report.get("realism_not_applicable", {}).items():
        lines.append(f"- `{k}`: not_applicable — _{reason}_")
    lines.append("")

    lines.append("## regression")
    if report["regression"] == NO_CANDIDATE:
        lines.append("_no_candidate — no cases found in eval/regression/_")
    else:
        for k, v in report["regression"].items():
            lines.append(f"- `{k}`: {'PASS' if v else 'FAIL'}")
    lines.append("")

    lines.append("## noise_rate_error")
    if report["noise_rate_error"] == NOT_APPLICABLE:
        lines.append("_not_applicable — no noisers implemented yet (Phase 3+)_")
    else:
        for k, v in report["noise_rate_error"].items():
            lines.append(f"- `{k}`: {v}")
    lines.append("")

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
