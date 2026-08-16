"""
Phase 3 redesign, Stage A step 2 — translate the candidate worklist built by
select_codemix_targets.py via the Anthropic Message Batches API (50% cost
reduction; the whole job is one submission and this repo's golden rule 5 —
"do not call a live endpoint in a loop" — is satisfied because this runs
ONCE, offline, and generation (src/noisers/codemix.py) never touches the
network; it only reads the frozen wordbank this script's output feeds into).

Per word, the model returns:
  {sinhala, english, codemix_plausible}
`codemix_plausible` is the naturalness gate: would a bilingual Sri Lankan
speaker actually say this English word inside a Sinhala sentence? Schema was
deliberately cut to these 3 fields (dropped pos/confidence/note, which an
early version carried) after a pilot-test cost measurement showed output
tokens — repeated per word across ~7,600 words — were the dominant cost
driver, not input; this is a bulk mechanical pass with a human review gate
downstream (build_codemix_usage_report.py) that has the worklist's example
sentences for context, so per-word self-reported confidence/notes weren't
pulling their weight in cost terms.

Automated quality gates run on every parsed result before it's accepted:
english non-empty and different from the input, contains an ASCII letter,
no stray Sinhala (except the attested "<English> එක*" construction already
used in the curated lexicon), codemix_plausible present and boolean.
Rejects go to codemix_translation_rejects.jsonl with a reason, not silently
dropped.

Requires ANTHROPIC_API_KEY in the environment (never hardcode it here).

Run:
  python scripts/translate_codemix_worklist.py --submit     # submit the batch, print batch id
  python scripts/translate_codemix_worklist.py --poll <id>  # poll until done, then collect
  python scripts/translate_codemix_worklist.py --collect <id>  # collect results now (batch must be ended)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time

from _codemix_common import LEXICON_DIR, load_curated_lexicon, log

WORKLIST_PATH = LEXICON_DIR / "codemix_translation_worklist.jsonl"
RESULTS_PATH = LEXICON_DIR / "codemix_translation_results.jsonl"
REJECTS_PATH = LEXICON_DIR / "codemix_translation_rejects.jsonl"
BATCH_ID_PATH = LEXICON_DIR / ".codemix_batch_id.txt"

MODEL = "claude-opus-5"
WORDS_PER_REQUEST = 80  # fewer, larger requests = fewer chances for a concurrent cache-miss on the shared prefix
MAX_EXAMPLES_IN_PROMPT = 1  # keep the per-request prompt compact; cost control
EXAMPLE_MAX_CHARS = 100  # examples are full SOLD posts; truncate to a snippet around the word

_ASCII_LETTER = re.compile(r"[A-Za-z]")
_SINHALA = re.compile(r"[඀-෿]")
# The one attested Sinhala-in-English-gloss pattern already used in the
# curated lexicon, e.g. "වැඩක් -> work එකක්": an English word followed by
# the Sinhala indefinite/definite particle එක and a case suffix.
_ALLOWED_SINHALA_TAIL = re.compile(r"^[A-Za-z][A-Za-z\s]*\s(එක[඀-෿]*)$")

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "translations": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "sinhala": {"type": "string"},
                    "english": {"type": "string", "description": "Best single-word/short-phrase English translation, or empty string if none is sensible."},
                    "codemix_plausible": {"type": "boolean", "description": "Would a bilingual Sri Lankan speaker actually substitute this English word into an otherwise-Sinhala sentence?"},
                },
                "required": ["sinhala", "english", "codemix_plausible"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["translations"],
    "additionalProperties": False,
}

SYSTEM_INSTRUCTIONS = """You are translating individual Sinhala words for a code-mixing noiser used in \
hate-speech-detection research (SOLD dataset). For each Sinhala word below, decide the best \
English translation AS IT WOULD BE CODE-MIXED into a Sinhala sentence by a real bilingual \
Sri Lankan social-media user — this is casual Sinhala-English code-mixing (Singlish), not \
formal dictionary translation.

Rules:
- english: the shortest natural English word/phrase a bilingual speaker would actually drop \
into a Sinhala sentence in place of this word. Empty string "" if there is no sensible \
single translation (e.g. the word is really a discourse particle, too polysemous, or an \
untranslatable idiom fragment that slipped past the candidate filter).
- codemix_plausible: true only if a real Sri Lankan bilingual speaker would plausibly say \
this English word inside a Sinhala sentence in casual text (tech/social/political/modern \
concepts code-mix heavily; basic everyday/traditional vocabulary — nature, food, body parts, \
household items — almost never does, even though the dictionary translation is fine). Err \
toward false when unsure — a missed substitution costs nothing, a bad one looks fake.
- If the word is a slur, ethnic/caste/religious insult, or vulgar term: set english to "" and \
codemix_plausible to false regardless of whether an English equivalent exists. Do not \
translate slurs.
- If the word is actually a verb inflection, pronoun, or function word that slipped through \
filtering: set codemix_plausible to false (english can still be filled in if obvious).

Below are worked examples from an existing hand-verified lexicon for this exact task, for \
calibration:"""


def _build_few_shot() -> str:
    curated = load_curated_lexicon()
    # Kept deliberately small (15 examples, not 40): the Batches API can
    # dispatch requests concurrently, and prompt caching has a documented
    # race — concurrent requests with an identical prefix can all miss the
    # cache and all pay the write premium, since a cache entry is only
    # readable after the FIRST response begins streaming (see
    # shared/prompt-caching.md's "Concurrent-request timing" note). Rather
    # than betting the ~$5 budget on caching behaving well across ~100
    # concurrently-dispatched requests, the cached prefix itself is kept
    # small enough that even a full cache-miss on every request stays cheap.
    sample = curated[::14][:15]
    lines = []
    for e in sample:
        lines.append(f'{{"sinhala": "{e["sinhala"]}", "english": "{e["english"]}", '
                      f'"source": "{e.get("source", "native")}"}}')
    return "\n".join(lines)


def _load_worklist() -> list[dict]:
    with WORKLIST_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _chunk(items: list, n: int) -> list[list]:
    return [items[i:i + n] for i in range(0, len(items), n)]


def _snippet(text: str, word: str, max_chars: int = EXAMPLE_MAX_CHARS) -> str:
    """A short window of `text` around the first occurrence of `word`, not
    the full post — full SOLD posts blew the per-request token budget ~3x
    over estimate (see LOG.md / plan pilot-test findings). Falls back to a
    plain head-truncation if the word isn't found as a substring (it should
    always be, since it came from tokenizing this same text, but grapheme
    clustering means a naive `str.find` is a reasonable, not guaranteed,
    match)."""
    if len(text) <= max_chars:
        return text
    idx = text.find(word)
    if idx == -1:
        return text[:max_chars] + "..."
    half = max_chars // 2
    start = max(0, idx - half)
    end = min(len(text), idx + len(word) + half)
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return prefix + text[start:end] + suffix


def _user_content(words: list[dict]) -> str:
    lines = ["Translate these Sinhala words:"]
    for w in words:
        examples = [_snippet(e, w["sinhala"]) for e in w.get("examples", [])[:MAX_EXAMPLES_IN_PROMPT]]
        ex_str = " | ".join(examples) if examples else "(no example available)"
        flags = []
        if w.get("verb_suspect"):
            flags.append("possible-verb-inflection")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        lines.append(f'- "{w["sinhala"]}" (freq={w["sold_frequency"]}){flag_str} — example usage: {ex_str}')
    return "\n".join(lines)


def _worklist_chunks() -> tuple[list[dict], list[list[dict]]]:
    worklist = _load_worklist()
    to_translate = [w for w in worklist if not w["already_verified"]]
    chunks = _chunk(to_translate, WORDS_PER_REQUEST)
    return to_translate, chunks


def cmd_test(n_chunks: int = 1) -> None:
    """Synchronous (non-batch) request against the first n_chunks chunks —
    validates the schema/prompt end-to-end and reports real token usage /
    implied cost BEFORE committing to the full batch submission. Not part
    of the frozen pipeline; a one-off sanity check."""
    import anthropic

    to_translate, chunks = _worklist_chunks()
    log("translate", f"{len(to_translate)} words total need translation; "
        f"testing on the first {n_chunks} chunk(s)")

    system_text = SYSTEM_INSTRUCTIONS + "\n" + _build_few_shot()
    client = anthropic.Anthropic()

    total_in = total_out = total_cache_read = total_cache_write = 0
    n_accepted = n_rejected = 0
    for i, chunk in enumerate(chunks[:n_chunks]):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
            system=[{
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral", "ttl": "1h"},
            }],
            messages=[{"role": "user", "content": _user_content(chunk)}],
        )
        u = resp.usage
        total_in += u.input_tokens
        total_out += u.output_tokens
        total_cache_read += (u.cache_read_input_tokens or 0)
        total_cache_write += (u.cache_creation_input_tokens or 0)
        text = next((b.text for b in resp.content if b.type == "text"), "{}")
        payload = json.loads(text)
        translations = payload.get("translations", [])
        log("translate", f"chunk {i}: {len(chunk)} words in, {len(translations)} translations out")
        for raw in translations:
            ok, reason = _validate(raw)
            n_accepted += ok
            n_rejected += not ok
        for raw in translations[:8]:
            ok, reason = _validate(raw)
            status = "OK" if ok else f"REJECT({reason})"
            print(f"  {raw.get('sinhala','?')!r:20s} -> {raw.get('english','?')!r:20s} "
                  f"plausible={raw.get('codemix_plausible')} [{status}]")
        log("translate", f"chunk {i}: input={u.input_tokens} output={u.output_tokens} "
            f"cache_read={u.cache_read_input_tokens} cache_write={u.cache_creation_input_tokens}")

    n_total_chunks = len(chunks)
    avg_in = total_in / n_chunks
    avg_out = total_out / n_chunks
    # cost model: first request of a fresh cache pays the write premium
    # (1.25x for 1h TTL... actually 2x for 1h TTL per docs), subsequent
    # requests pay ~0.1x read on the cached portion. Report a simple
    # uncached-worst-case AND an all-cached-best-case bound.
    price_in, price_out = 5.00, 25.00  # $/MTok, opus-5, standard (non-batch) rate
    worst_case = (avg_in * n_total_chunks / 1e6) * price_in + (avg_out * n_total_chunks / 1e6) * price_out
    batch_worst_case = worst_case / 2  # batches API is 50% off
    log("translate", f"--- projection over all {n_total_chunks} chunks ---")
    log("translate", f"avg input/chunk={avg_in:.0f} avg output/chunk={avg_out:.0f}")
    log("translate", f"worst-case (no cache hits, standard rate): ${worst_case:.2f}")
    log("translate", f"worst-case via Batches API (50% off): ${batch_worst_case:.2f}")


def cmd_submit() -> None:
    import anthropic

    to_translate, chunks = _worklist_chunks()
    log("translate", f"{len(to_translate)} words need translation")
    log("translate", f"{len(chunks)} batch requests of up to {WORDS_PER_REQUEST} words each")

    system_text = SYSTEM_INSTRUCTIONS + "\n" + _build_few_shot()

    client = anthropic.Anthropic()
    from anthropic.types.message_create_params import MessageCreateParamsNonStreaming
    from anthropic.types.messages.batch_create_params import Request

    requests = []
    for i, chunk in enumerate(chunks):
        requests.append(Request(
            custom_id=f"chunk-{i:04d}",
            params=MessageCreateParamsNonStreaming(
                model=MODEL,
                max_tokens=8000,
                thinking={"type": "disabled"},
                output_config={"effort": "low", "format": {"type": "json_schema", "schema": RESPONSE_SCHEMA}},
                system=[{
                    "type": "text",
                    "text": system_text,
                    "cache_control": {"type": "ephemeral", "ttl": "1h"},
                }],
                messages=[{"role": "user", "content": _user_content(chunk)}],
            ),
        ))

    batch = client.messages.batches.create(requests=requests)
    BATCH_ID_PATH.write_text(batch.id, encoding="utf-8")
    log("translate", f"submitted batch {batch.id} ({len(requests)} requests) -> status {batch.processing_status}")
    log("translate", f"batch id saved to {BATCH_ID_PATH}; poll with --poll {batch.id}")


def cmd_poll(batch_id: str, interval_s: int = 30) -> None:
    import anthropic
    client = anthropic.Anthropic()
    while True:
        batch = client.messages.batches.retrieve(batch_id)
        counts = batch.request_counts
        log("translate", f"status={batch.processing_status} "
            f"processing={counts.processing} succeeded={counts.succeeded} "
            f"errored={counts.errored} canceled={counts.canceled} expired={counts.expired}")
        if batch.processing_status == "ended":
            break
        time.sleep(interval_s)
    cmd_collect(batch_id)


def _reject(reason: str, raw: dict, rejects: list) -> None:
    rejects.append({"sinhala": raw.get("sinhala", "?"), "reason": reason, "raw": raw})


def _validate(raw: dict) -> tuple[bool, str]:
    sinhala = raw.get("sinhala", "")
    english = (raw.get("english") or "").strip()
    if not english:
        return False, "empty english (model judged no translation)"
    if english == sinhala:
        return False, "english identical to sinhala input"
    if not _ASCII_LETTER.search(english):
        return False, "english contains no ASCII letters"
    if _SINHALA.search(english) and not _ALLOWED_SINHALA_TAIL.match(english):
        return False, "stray Sinhala script in english (not the attested '<word> එක*' construction)"
    if not isinstance(raw.get("codemix_plausible"), bool):
        return False, "codemix_plausible missing or not boolean"
    return True, ""


def cmd_collect(batch_id: str) -> None:
    import anthropic
    client = anthropic.Anthropic()

    worklist_by_word = {w["sinhala"]: w for w in _load_worklist()}
    accepted: list[dict] = []
    rejects: list[dict] = []
    n_errored = 0

    for result in client.messages.batches.results(batch_id):
        if result.result.type != "succeeded":
            n_errored += 1
            log("translate", f"[{result.custom_id}] {result.result.type} — not collected")
            continue
        msg = result.result.message
        text = next((b.text for b in msg.content if b.type == "text"), None)
        if text is None:
            n_errored += 1
            continue
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            n_errored += 1
            log("translate", f"[{result.custom_id}] response was not valid JSON — skipped")
            continue

        for raw in payload.get("translations", []):
            ok, reason = _validate(raw)
            source_row = worklist_by_word.get(raw.get("sinhala", ""))
            if not ok:
                _reject(reason, raw, rejects)
                continue
            accepted.append({
                "sinhala": raw["sinhala"],
                "english": raw["english"].strip(),
                "source": "llm",
                "codemix_plausible": bool(raw["codemix_plausible"]),
                "sold_frequency": source_row["sold_frequency"] if source_row else 0,
                "evidence": f"llm-translated (batch {batch_id})",
            })

    with RESULTS_PATH.open("w", encoding="utf-8") as f:
        for row in accepted:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with REJECTS_PATH.open("w", encoding="utf-8") as f:
        for row in rejects:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    log("translate", f"accepted {len(accepted)}, rejected {len(rejects)}, "
        f"{n_errored} request-level errors -> {RESULTS_PATH}")
    log("translate", f"rejects with reasons -> {REJECTS_PATH}")

    n_plausible = sum(1 for r in accepted if r["codemix_plausible"])
    log("translate", f"{n_plausible}/{len(accepted)} accepted translations marked codemix_plausible=true")


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", type=int, metavar="N_CHUNKS", nargs="?", const=1,
                        help="synchronous sanity check on the first N_CHUNKS chunks (default 1); no batch submitted")
    group.add_argument("--submit", action="store_true")
    group.add_argument("--poll", metavar="BATCH_ID")
    group.add_argument("--collect", metavar="BATCH_ID")
    args = parser.parse_args()

    if args.test is not None:
        cmd_test(args.test)
    elif args.submit:
        cmd_submit()
    elif args.poll:
        cmd_poll(args.poll)
    elif args.collect:
        cmd_collect(args.collect)


if __name__ == "__main__":
    main()
