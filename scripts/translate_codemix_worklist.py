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

--- Round 5: extended to phrases (--kind phrase) ---
scripts/mine_codemix_phrases.py produces data/lexicon/codemix_phrase_worklist.jsonl
in the SAME shape _user_content() already reads (sinhala, sold_frequency,
verb_suspect, examples), so no schema change was needed -- only a second
set of output paths (so a phrase batch can never collide with or overwrite
word results) and phrase-specific system instructions (see
_SYSTEM_INSTRUCTIONS_BY_KIND). `--pilot N` draws a deterministic stratified
sample of N candidates (stratified by n_words and by a frequency quartile,
seeded) instead of the full worklist -- this is what Stage 2 of the round 5
plan uses to measure the REAL phrase-survival rate on 300 phrases before
committing the full ~8,700-phrase translation budget.

Requires ANTHROPIC_API_KEY in the environment (never hardcode it here).

Run:
  python scripts/translate_codemix_worklist.py --submit                    # words, full worklist
  python scripts/translate_codemix_worklist.py --kind phrase --pilot 300 --submit   # phrase pilot
  python scripts/translate_codemix_worklist.py --kind phrase --submit      # phrases, full worklist
  python scripts/translate_codemix_worklist.py [--kind phrase] --poll <id>     # poll until done, then collect
  python scripts/translate_codemix_worklist.py [--kind phrase] --collect <id>  # collect results now (batch must be ended)
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from _codemix_common import LEXICON_DIR, load_curated_lexicon, log

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

_WORD_SYSTEM_INSTRUCTIONS = """You are translating individual Sinhala words for a code-mixing noiser used in \
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

# Round 5: the phrase variant. Same task, same output shape (a phrase's
# "sinhala" field is the space-joined 2-3 word span mined by
# scripts/mine_codemix_phrases.py), different framing -- a phrase
# translation stands in for the WHOLE span in one switch, so naturalness
# has to be judged as a unit, not word-by-word, and the model is told the
# span may legitimately include a Sinhala particle (the attested
# content-word + "එක" pattern) rather than being pure English throughout.
_PHRASE_SYSTEM_INSTRUCTIONS = """You are translating short Sinhala PHRASES (2-3 words, mined as \
frequently-recurring contiguous spans from real SOLD social-media posts) for a code-mixing \
noiser used in hate-speech-detection research. For each phrase below, decide the best English \
rendering AS IT WOULD BE CODE-MIXED into a Sinhala sentence by a real bilingual Sri Lankan \
social-media user, replacing the WHOLE phrase as one switched unit — this is casual \
Sinhala-English code-mixing (Singlish), not formal dictionary translation, and not a \
word-by-word gloss.

Rules:
- english: the shortest natural English rendering a bilingual speaker would actually drop into \
a Sinhala sentence in place of the WHOLE phrase (e.g. a Sinhala verb phrase might become a \
short English predicate; a Sinhala noun phrase might become an English noun phrase). Empty \
string "" if the phrase doesn't work as a single switched unit (e.g. it's really two \
independent words that happen to be adjacent, or it's a fixed Sinhala idiom with no natural \
English equivalent as a unit).
- codemix_plausible: true only if a real Sri Lankan bilingual speaker would plausibly switch \
this ENTIRE phrase into English as one unit in casual text — not just whether the individual \
words are each individually plausible. A phrase where only one word would realistically \
code-mix (the other staying Sinhala) should get codemix_plausible=false here, even if english \
is filled in for reference — that's the unigram mechanism's job, not this one's. Err toward \
false when unsure.
- If the phrase contains a slur, ethnic/caste/religious insult, or vulgar term: set english to \
"" and codemix_plausible to false regardless of whether an English equivalent exists.
- A phrase flagged [possible-verb-inflection] may still be plausible as a switched ENGLISH \
PREDICATE (e.g. a full verb phrase borrowed wholesale) even though round 4 of this project \
rejects bare English verbs bolted onto Sinhala grammar — those are different phenomena; judge \
this phrase on whether the WHOLE English rendering reads as something a real bilingual speaker \
would actually type, not by that unrelated rule.

Below are worked examples from an existing hand-verified SINGLE-WORD lexicon for this project \
(for calibration of tone/register only — these are words, not phrases):"""

_SYSTEM_INSTRUCTIONS_BY_KIND = {"word": _WORD_SYSTEM_INSTRUCTIONS, "phrase": _PHRASE_SYSTEM_INSTRUCTIONS}


@dataclass(frozen=True)
class _Config:
    kind: str
    worklist_path: Path
    results_path: Path
    rejects_path: Path
    batch_id_path: Path
    system_instructions: str
    item_noun: str


def _config(kind: str) -> _Config:
    if kind == "word":
        return _Config(
            kind="word",
            worklist_path=LEXICON_DIR / "codemix_translation_worklist.jsonl",
            results_path=LEXICON_DIR / "codemix_translation_results.jsonl",
            rejects_path=LEXICON_DIR / "codemix_translation_rejects.jsonl",
            batch_id_path=LEXICON_DIR / ".codemix_batch_id.txt",
            system_instructions=_SYSTEM_INSTRUCTIONS_BY_KIND["word"],
            item_noun="word",
        )
    if kind == "phrase":
        return _Config(
            kind="phrase",
            worklist_path=LEXICON_DIR / "codemix_phrase_worklist.jsonl",
            results_path=LEXICON_DIR / "codemix_phrase_translation_results.jsonl",
            rejects_path=LEXICON_DIR / "codemix_phrase_translation_rejects.jsonl",
            batch_id_path=LEXICON_DIR / ".codemix_phrase_batch_id.txt",
            system_instructions=_SYSTEM_INSTRUCTIONS_BY_KIND["phrase"],
            item_noun="phrase",
        )
    raise ValueError(f"unknown kind {kind!r}, expected 'word' or 'phrase'")


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


def _load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def _load_worklist(cfg: _Config) -> list[dict]:
    return _load_jsonl(cfg.worklist_path)


def _already_translated_keys(cfg: _Config) -> set[str]:
    """sinhala keys already present in results_path from a PRIOR run of this
    kind -- e.g. the round-5 phrase pilot (300 rows) followed later by the
    full ~8,700-row batch. Without this, a second batch would silently
    re-translate and re-spend budget on everything the pilot already
    covered (bug fixed in round 5 -- the original word-kind code only ever
    checked `already_verified`, a flag that's permanently false for every
    phrase row since no pre-existing curated phrase source exists)."""
    return {row["sinhala"] for row in _load_jsonl(cfg.results_path)}


def _chunk(items: list, n: int) -> list[list]:
    return [items[i:i + n] for i in range(0, len(items), n)]


def _stratified_pilot_sample(items: list[dict], n: int, seed: int = 1337) -> list[dict]:
    """Deterministic stratified sample of `n` items for a pilot batch (round
    5 Stage 2: 300 phrases, to measure the REAL survival rate before
    committing the full translation budget -- see the plan).

    Stratified two ways so the pilot isn't dominated by one slice: by
    n_words (bigram vs trigram, sampled in the same proportion as the full
    pool) and by SOLD-frequency quartile within each n_words group (so the
    pilot isn't just "the 300 most frequent phrases," which would bias the
    measured survival rate upward relative to the full worklist's long tail).
    Falls back to plain sampling for word-kind worklists, which don't carry
    n_words at all."""
    if not items or "n_words" not in items[0]:
        rng = random.Random(seed)
        pool = items[:]
        rng.shuffle(pool)
        return pool[:n]

    by_n_words: dict[int, list[dict]] = {}
    for it in items:
        by_n_words.setdefault(it["n_words"], []).append(it)

    out: list[dict] = []
    rng = random.Random(seed)
    for n_words, group in sorted(by_n_words.items()):
        share = round(n * len(group) / len(items))
        group_sorted = sorted(group, key=lambda it: it["sold_frequency"])
        quartiles = _chunk(group_sorted, max(1, -(-len(group_sorted) // 4)))
        # round-robin draw across quartiles so each frequency band
        # contributes roughly evenly, not just the top quartile by volume
        picked: list[dict] = []
        qi = 0
        shuffled_quartiles = [q[:] for q in quartiles]
        for q in shuffled_quartiles:
            rng.shuffle(q)
        while len(picked) < share and any(shuffled_quartiles):
            q = shuffled_quartiles[qi % len(shuffled_quartiles)]
            if q:
                picked.append(q.pop())
            qi += 1
            if qi > 10 * share + 100:  # safety valve against an infinite loop on exhausted groups
                break
        out.extend(picked)
    rng.shuffle(out)
    return out[:n]


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


def _user_content(cfg: _Config, items: list[dict]) -> str:
    noun = cfg.item_noun
    lines = [f"Translate these Sinhala {noun}s:"]
    for w in items:
        examples = [_snippet(e, w["sinhala"]) for e in w.get("examples", [])[:MAX_EXAMPLES_IN_PROMPT]]
        ex_str = " | ".join(examples) if examples else "(no example available)"
        flags = []
        if w.get("verb_suspect"):
            flags.append("possible-verb-inflection")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        lines.append(f'- "{w["sinhala"]}" (freq={w["sold_frequency"]}){flag_str} — example usage: {ex_str}')
    return "\n".join(lines)


def _worklist_chunks(cfg: _Config, pilot: int | None) -> tuple[list[dict], list[list[dict]]]:
    worklist = _load_worklist(cfg)
    already_verified = {w["sinhala"] for w in worklist if w.get("already_verified")}
    already_translated = _already_translated_keys(cfg)
    skip = already_verified | already_translated
    to_translate = [w for w in worklist if w["sinhala"] not in skip]
    n_skipped_translated = sum(1 for w in worklist if w["sinhala"] in already_translated)
    if n_skipped_translated:
        log("translate", f"skipping {n_skipped_translated} {cfg.item_noun}s already present in "
            f"{cfg.results_path.name} from a prior run of this kind")
    if pilot is not None:
        to_translate = _stratified_pilot_sample(to_translate, pilot)
        log("translate", f"--pilot {pilot}: stratified sample drawn, "
            f"{len(to_translate)} {cfg.item_noun}s selected")
    chunks = _chunk(to_translate, WORDS_PER_REQUEST)
    return to_translate, chunks


def cmd_test(cfg: _Config, n_chunks: int = 1, pilot: int | None = None) -> None:
    """Synchronous (non-batch) request against the first n_chunks chunks —
    validates the schema/prompt end-to-end and reports real token usage /
    implied cost BEFORE committing to the full batch submission. Not part
    of the frozen pipeline; a one-off sanity check."""
    import anthropic

    to_translate, chunks = _worklist_chunks(cfg, pilot)
    log("translate", f"{len(to_translate)} {cfg.item_noun}s total need translation; "
        f"testing on the first {n_chunks} chunk(s)")

    system_text = cfg.system_instructions + "\n" + _build_few_shot()
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
            messages=[{"role": "user", "content": _user_content(cfg, chunk)}],
        )
        u = resp.usage
        total_in += u.input_tokens
        total_out += u.output_tokens
        total_cache_read += (u.cache_read_input_tokens or 0)
        total_cache_write += (u.cache_creation_input_tokens or 0)
        text = next((b.text for b in resp.content if b.type == "text"), "{}")
        payload = json.loads(text)
        translations = payload.get("translations", [])
        log("translate", f"chunk {i}: {len(chunk)} {cfg.item_noun}s in, {len(translations)} translations out")
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


def cmd_submit(cfg: _Config, pilot: int | None = None) -> None:
    import anthropic

    to_translate, chunks = _worklist_chunks(cfg, pilot)
    log("translate", f"{len(to_translate)} {cfg.item_noun}s need translation")
    log("translate", f"{len(chunks)} batch requests of up to {WORDS_PER_REQUEST} {cfg.item_noun}s each")
    if not to_translate:
        log("translate", "nothing to submit -- worklist empty after already-translated skip")
        return

    system_text = cfg.system_instructions + "\n" + _build_few_shot()

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
                messages=[{"role": "user", "content": _user_content(cfg, chunk)}],
            ),
        ))

    batch = client.messages.batches.create(requests=requests)
    cfg.batch_id_path.write_text(batch.id, encoding="utf-8")
    log("translate", f"submitted batch {batch.id} ({len(requests)} requests) -> status {batch.processing_status}")
    log("translate", f"batch id saved to {cfg.batch_id_path}; poll with --kind {cfg.kind} --poll {batch.id}")


def cmd_poll(cfg: _Config, batch_id: str, interval_s: int = 30) -> None:
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
    cmd_collect(cfg, batch_id)


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


def cmd_collect(cfg: _Config, batch_id: str) -> None:
    import anthropic
    client = anthropic.Anthropic()

    worklist_by_word = {w["sinhala"]: w for w in _load_worklist(cfg)}
    # MERGE, never overwrite: results_path may already hold accepted rows
    # from an earlier batch of this same kind (e.g. the round-5 phrase
    # pilot, collected before the full batch runs) -- opening with "w" here
    # was the original bug (see module docstring's "Round 5" section) that
    # would have silently destroyed those. Same last-write-wins precedent
    # scripts/build_codemix_wordbank.py already uses for its correction
    # layer: a re-translated sinhala key in THIS batch overwrites the
    # earlier row, everything else carries forward untouched.
    existing_by_key = {row["sinhala"]: row for row in _load_jsonl(cfg.results_path)}
    new_accepted: list[dict] = []
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
            new_accepted.append({
                "sinhala": raw["sinhala"],
                "english": raw["english"].strip(),
                "source": "llm",
                "codemix_plausible": bool(raw["codemix_plausible"]),
                "sold_frequency": source_row["sold_frequency"] if source_row else 0,
                "evidence": f"llm-translated (batch {batch_id})",
            })

    merged = dict(existing_by_key)
    for row in new_accepted:
        merged[row["sinhala"]] = row

    with cfg.results_path.open("w", encoding="utf-8") as f:
        for row in merged.values():
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # rejects DO overwrite (they're per-batch diagnostics, not accumulated
    # state anything downstream depends on carrying forward)
    with cfg.rejects_path.open("w", encoding="utf-8") as f:
        for row in rejects:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    log("translate", f"this batch: accepted {len(new_accepted)}, rejected {len(rejects)}, "
        f"{n_errored} request-level errors")
    log("translate", f"{cfg.results_path} now holds {len(merged)} {cfg.item_noun}s total "
        f"({len(existing_by_key)} carried forward + {len(merged) - len(existing_by_key)} new/updated)")
    log("translate", f"rejects with reasons -> {cfg.rejects_path}")

    n_plausible = sum(1 for r in merged.values() if r["codemix_plausible"])
    log("translate", f"{n_plausible}/{len(merged)} accepted translations marked codemix_plausible=true")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kind", choices=["word", "phrase"], default="word",
                         help="translate the word worklist (default) or the round-5 phrase worklist")
    parser.add_argument("--pilot", type=int, metavar="N", default=None,
                         help="draw a deterministic stratified sample of N items instead of the full "
                              "worklist (round 5 Stage 2: --kind phrase --pilot 300); only meaningful "
                              "with --test/--submit")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", type=int, metavar="N_CHUNKS", nargs="?", const=1,
                        help="synchronous sanity check on the first N_CHUNKS chunks (default 1); no batch submitted")
    group.add_argument("--submit", action="store_true")
    group.add_argument("--poll", metavar="BATCH_ID")
    group.add_argument("--collect", metavar="BATCH_ID")
    args = parser.parse_args()

    cfg = _config(args.kind)

    if args.test is not None:
        cmd_test(cfg, args.test, pilot=args.pilot)
    elif args.submit:
        cmd_submit(cfg, pilot=args.pilot)
    elif args.poll:
        cmd_poll(cfg, args.poll)
    elif args.collect:
        cmd_collect(cfg, args.collect)


if __name__ == "__main__":
    main()
