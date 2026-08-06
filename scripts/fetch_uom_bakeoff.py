"""
DELIBERATE EXCEPTION to the "no live calls in a loop" rule that governs
this repo — same exception class as scripts/demo_live_uom.py, but for the
actual Phase 1 gold_cer bake-off rather than an ad-hoc demo.

Phase 1's original bake-off scored `uom_rules` (a local reimplementation
calibrated against a 20-item sample of the live site) as a stand-in for
the real UoM Sinhala Romaniser. That's a mock, not the genuine article, in
what should be a real comparison — this fetches
the REAL site's output for the entire gold set (2000 words +
400 sentences = 2400 items, the same population every other backend was
already scored on), ONE TIME, and caches it so the harness never calls the
live site again.

Run:  python scripts/fetch_uom_bakeoff.py
      python scripts/fetch_uom_bakeoff.py --delay 0.5   # slower, more polite
      python scripts/fetch_uom_bakeoff.py --force       # re-fetch everything, ignore cache

Resumable: writes each result to data/gold/uom_live_bakeoff.jsonl
immediately (flushed per line), and skips any Sinhala string already
present in that file on a re-run — so an interrupted ~20-minute run over
someone else's server doesn't mean starting over. This is the ONLY script
in the repo that calls the live endpoint at this scale; eval/gold_cer.py's
`uom_live` backend only ever reads the cache this script produces.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.demo_live_uom import call_live_uom  # noqa: E402

GOLD_DIR = REPO_ROOT / "data" / "gold"
GOLD_WORDS_PATH = GOLD_DIR / "gold_words.jsonl"
GOLD_SENTENCES_PATH = GOLD_DIR / "gold_sentences.jsonl"
CACHE_PATH = GOLD_DIR / "uom_live_bakeoff.jsonl"

DEFAULT_DELAY = 0.3
MAX_RETRIES = 3
PROGRESS_EVERY = 100


def log(msg: str) -> None:
    print(f"[fetch_uom_bakeoff] {msg}")


def _load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_targets() -> list[str]:
    """All 2000 gold words + 400 gold sentences — the exact population
    every other bake-off backend was already scored on."""
    words = [row["sinhala"] for row in _load_jsonl(GOLD_WORDS_PATH)]
    sentences = [row["sinhala"] for row in _load_jsonl(GOLD_SENTENCES_PATH)]
    return words + sentences


def load_cache() -> dict[str, str]:
    if not CACHE_PATH.exists():
        return {}
    with CACHE_PATH.open(encoding="utf-8") as f:
        return {
            row["sinhala"]: row["live_output"]
            for row in (json.loads(line) for line in f if line.strip())
        }


def fetch_with_retry(text: str) -> str | None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return call_live_uom(text, remove_diacritics=True)
        except Exception as e:  # noqa: BLE001 - long unattended run must not die on one bad request
            log(f"attempt {attempt}/{MAX_RETRIES} failed for {text[:40]!r}: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(1.0 * attempt)
    return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY,
                         help=f"seconds to wait between requests (default {DEFAULT_DELAY})")
    parser.add_argument("--force", action="store_true",
                         help="ignore the existing cache and re-fetch every item")
    args = parser.parse_args()

    targets = load_targets()
    cache = {} if args.force else load_cache()
    remaining = [t for t in targets if t not in cache]

    log(f"{len(targets)} total gold items, {len(cache)} already cached, {len(remaining)} to fetch")
    if not remaining:
        log("nothing to do — cache already complete.")
        return

    failed = []
    with CACHE_PATH.open("a", encoding="utf-8") as f:
        for i, text in enumerate(remaining, 1):
            live_output = fetch_with_retry(text)
            if live_output is None:
                failed.append(text)
                log(f"giving up on {text[:40]!r} after {MAX_RETRIES} attempts")
            else:
                f.write(json.dumps({"sinhala": text, "live_output": live_output}, ensure_ascii=False) + "\n")
                f.flush()
            if i % PROGRESS_EVERY == 0 or i == len(remaining):
                log(f"{i}/{len(remaining)} fetched this run ({len(failed)} failed so far)")
            time.sleep(args.delay)

    log(f"done. {len(remaining) - len(failed)} fetched, {len(failed)} failed this run.")
    if failed:
        log(f"failed items (re-run this script to retry just these — cache skips completed ones): {failed[:10]}")


if __name__ == "__main__":
    main()
