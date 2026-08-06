"""
DELIBERATE EXCEPTION to the "no live calls in the loop" rule that governs
the rest of this repo (the live UoM PHP endpoint is never called in a
loop or by the harness — see below).

This script calls the REAL website — https://nisansads.staff.uom.lk/
CodeSamples/sinhala_romaniser.php — directly, for manual testing/demo
purposes only. It is intentionally separate from everything else in this
repo:
  - src/romanizers/uom_rules.py (the local reimplementation, calibrated
    once against the site — see scripts/verify_uom_endpoint.py) is what the
    Phase 1 bake-off actually scored, and it lost to aksharamukha.
  - The real generation pipeline (src/noisers/transliteration.py,
    scripts/generate_transliteration.py) uses aksharamukha, never this
    script or uom_rules.py.
  - This script is not wired into any loop, batch job, or the harness —
    it only ever runs against whatever small input is explicitly given to
    it, on demand.

Run:
  python scripts/demo_live_uom.py                                  # uses data/demo/demo_paragraphs.json
  python scripts/demo_live_uom.py --input path/to/your.json         # any JSON list of strings
  python scripts/demo_live_uom.py --text "ලංකාව සුන්දරයි"            # a single ad-hoc string
  python scripts/demo_live_uom.py --keep-diacritics                 # default sends remove_diacritics=1
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ENDPOINT_URL = "https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php"
DEFAULT_INPUT = REPO_ROOT / "data" / "demo" / "demo_paragraphs.json"

_OUTPUT_RE = re.compile(r'<div class="output-box"[^>]*>(.*?)</div>\s*</div>', re.S)


def call_live_uom(sinhala_text: str, remove_diacritics: bool = True) -> str:
    """POST directly to the live UoM Sinhala Romaniser and return its output.
    Makes one real HTTP request per call — this is the whole point of this
    script, which exists specifically to test the actual website."""
    data = {"sinhala_text": sinhala_text}
    if remove_diacritics:
        data["remove_diacritics"] = "1"
    resp = requests.post(ENDPOINT_URL, data=data, timeout=30)
    resp.raise_for_status()
    match = _OUTPUT_RE.search(resp.text)
    if not match:
        raise RuntimeError(f"could not find output-box in response for {sinhala_text!r}")
    raw = re.sub(r"<[^>]+>", "", match.group(1))
    return html.unescape(raw).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT,
                         help=f"JSON list of strings to romanize (default: {DEFAULT_INPUT})")
    parser.add_argument("--text", type=str, default=None,
                         help="romanize a single ad-hoc string instead of reading --input")
    parser.add_argument("--keep-diacritics", action="store_true",
                         help="don't send remove_diacritics=1 (get the formal IAST-style output instead)")
    args = parser.parse_args()

    if args.text is not None:
        parts = [args.text]
    else:
        parts = json.loads(args.input.read_text(encoding="utf-8"))

    print(f"[demo_live_uom] calling the LIVE site at {ENDPOINT_URL} for {len(parts)} item(s)...")
    for i, text in enumerate(parts):
        live_output = call_live_uom(text, remove_diacritics=not args.keep_diacritics)
        print(f"--- part {i} ---")
        print("ORIGINAL:", text)
        print("LIVE UOM:", live_output)
        print()


if __name__ == "__main__":
    main()
