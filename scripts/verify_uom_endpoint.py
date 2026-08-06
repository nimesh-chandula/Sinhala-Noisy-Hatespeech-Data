"""
ONE-TIME live verification of the UoM Sinhala Romaniser endpoint, per the
project rule: do not call the live UoM PHP endpoint in a loop — instead,
reimplement its ruleset locally in Python, verify the reimplementation
matches the web tool on a 20-item sample once, then use the local version.

Endpoint: https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php
(Sinhala Unicode -> romanized text; POST `sinhala_text` + `remove_diacritics=1`
for plain-ASCII output, which is the target style — the default mode adds
IAST-style diacritics nobody types casually.)

Two modes:
  python scripts/verify_uom_endpoint.py            # fetch (the ONE-TIME network step)
  python scripts/verify_uom_endpoint.py --diff      # compare saved live output against
                                                     # the local src/romanizers/uom_rules.py
                                                     # reimplementation — run this as many
                                                     # times as needed while calibrating;
                                                     # it never touches the network.

`fetch` mode is idempotent by cache: if data/gold/uom_endpoint_verification.jsonl
already exists, it refuses to re-run (use --force to override) — this is the
one call this project ever makes to the live endpoint, and it should stay that way.
"""

from __future__ import annotations

import argparse
import html
import json
import random
import re
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import clusters  # noqa: E402

GOLD_DIR = REPO_ROOT / "data" / "gold"
GOLD_WORDS_PATH = GOLD_DIR / "gold_words.jsonl"
GOLD_SENTENCES_PATH = GOLD_DIR / "gold_sentences.jsonl"
VERIFICATION_PATH = GOLD_DIR / "uom_endpoint_verification.jsonl"

ENDPOINT_URL = "https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php"
SEED = 1337
N_WORDS = 10
N_SENTENCES = 10

_OUTPUT_RE = re.compile(r'<div class="output-box"[^>]*>(.*?)</div>\s*</div>', re.S)


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def select_sample() -> list[str]:
    """Deterministically pick N_WORDS + N_SENTENCES Sinhala strings, seed=1337."""
    words = [row["sinhala"] for row in _load_jsonl(GOLD_WORDS_PATH)]
    sentences = [row["sinhala"] for row in _load_jsonl(GOLD_SENTENCES_PATH)]
    rng = random.Random(SEED)
    picked_words = rng.sample(sorted(words), N_WORDS)
    picked_sentences = rng.sample(sorted(sentences), N_SENTENCES)
    return picked_words + picked_sentences


def call_endpoint(sinhala_text: str) -> str:
    resp = requests.post(
        ENDPOINT_URL,
        data={"sinhala_text": sinhala_text, "remove_diacritics": "1"},
        timeout=30,
    )
    resp.raise_for_status()
    match = _OUTPUT_RE.search(resp.text)
    if not match:
        raise RuntimeError(f"could not find output-box in response for {sinhala_text!r}")
    # Strip the placeholder span if echoed back empty, any stray HTML, and
    # un-escape entities (the page echoes input back HTML-escaped, e.g. ' -> &#039;).
    raw = match.group(1)
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = html.unescape(raw)
    return raw.strip()


def fetch(force: bool = False) -> None:
    if VERIFICATION_PATH.exists() and not force:
        print(f"[verify_uom_endpoint] {VERIFICATION_PATH} already exists — refusing to "
              f"re-call the live endpoint. Use --force to override.")
        return
    sample = select_sample()
    results = []
    for text in sample:
        live_output = call_endpoint(text)
        results.append({"sinhala": text, "live_output": live_output})
        print(f"[verify_uom_endpoint] {text!r} -> {live_output!r}")
    with VERIFICATION_PATH.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"[verify_uom_endpoint] wrote {len(results)} rows -> {VERIFICATION_PATH}")
    print("[verify_uom_endpoint] DONE. The live endpoint should not be called again "
          "— use --diff against this saved file from now on.")


def diff() -> None:
    if not VERIFICATION_PATH.exists():
        print(f"[verify_uom_endpoint] {VERIFICATION_PATH} not found — run without "
              f"--diff first to fetch the one-time sample.")
        return
    try:
        from src.romanizers.uom_rules import romanize
    except (ImportError, NotImplementedError) as e:
        print(f"[verify_uom_endpoint] src/romanizers/uom_rules.py not ready yet: {e}")
        return

    rows = _load_jsonl(VERIFICATION_PATH)
    n_exact = 0
    for row in rows:
        local_output = romanize(row["sinhala"])
        exact = local_output == row["live_output"]
        n_exact += exact
        marker = "OK  " if exact else "DIFF"
        print(f"[{marker}] {row['sinhala']!r}")
        print(f"        live : {row['live_output']!r}")
        print(f"        local: {local_output!r}")
    print(f"\n[verify_uom_endpoint] {n_exact}/{len(rows)} exact matches")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--diff", action="store_true", help="compare local uom_rules.py against the saved sample (no network)")
    parser.add_argument("--force", action="store_true", help="re-fetch from the live endpoint even if already cached")
    args = parser.parse_args()

    if args.diff:
        diff()
    else:
        fetch(force=args.force)


if __name__ == "__main__":
    main()
