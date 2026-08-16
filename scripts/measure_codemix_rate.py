"""
Phase 3 step 1 — measure the NATURAL rate of English-word insertion into
Sinhala/Singlish text, before writing a single line of noiser code. Per
CLAUDE.md golden rule 6, severity targets must be justified by something
measured, not assumed — this script is that measurement.

Two corpora are examined:
  1. data/reference/reference_singlish.txt — real, human-typed romanized
     Sinhala (Swa-Bhasha sentence pairs). Already entirely Latin-script, so
     "is this token English or romanized Sinhala" is the only question.
  2. data/sold/{train,test}.jsonl — the actual corpus this project noises.
     Sinhala-script text with some Latin-script residue. That residue is
     NOT all authored code-mixing: Twitter scraping left artifacts behind
     (@USER/URL placeholders, embedded quoted-tweet headers like
     "V I S H W A @USER  ·  13 Aug 2018", "Show this thread"). Both a raw
     and a cleaned rate are reported so the cleaning's effect is visible,
     not hidden.

--- How "is this token English" is decided, without an English dictionary ---
No Sinhala-English dictionary exists anywhere in this repo (see
docs/research_documentation.md §2) and LOG.md already records that
automated English-wordlist matching against Sinhala romanizations produces
majority false positives on this exact data (coincidental collisions like
"ganga"/"gang", "gena"/"gen"). So instead of an external wordlist, this
script uses data ALREADY in the repo as a NEGATIVE filter: every romanized
form Swa-Bhasha attests for some real Sinhala word (data/raw/swabhasha_words.csv,
450K+ distinct Sinhala words, ~7.1M romanized-spelling pairs) is treated as
"known Sinhala-in-Latin-script" and excluded. A Latin token that survives
that filter — i.e. is NOT how any real Sinhala word is known to be spelled
— is a CANDIDATE English token. This can't achieve perfect precision (rare
Sinhala words this large-but-not-exhaustive corpus never happened to
attest will slip through as false candidates), but it fails in the SAFE
direction: real English usage already sitting in the 123-entry
`_LOANWORD_OVERRIDES` table is unioned back in regardless of the filter
outcome, and every candidate this script surfaces still gets hand-verified
in scripts/build_codemix_lexicon.py before being trusted — this script
only ranks candidates and measures rates, it decides nothing on its own.

--- A second, stronger attestation channel: the "eka" construction ---
Sinhala is agglutinative and attaches case particles to a bare noun stem
via the light noun "එක" (e.g. "පොත" (book) + dative -> "පොතට"; an
English stem substituted the same way is "book එකට", not a romanized
"eka"). Scanning SOLD directly for `<Latin word> එක[case-suffix]` finds
555 real instances (photo, phone, film, wedding, song, group, app,
profile, page, paper, life, vaccine, service, comment, team, game, ...)
— i.e. this exact construction is already how real posters code-mix in
THIS corpus. A word attested this way is even better evidence than a bare
Latin-token count: it's not just "this English word appears somewhere",
it's "this English word was already used in the exact grammatical
construction the noiser will produce." Some words (song, bus, game,
channel) show 0 in the plain Latin-token count above only because they
coincidentally collide with an unrelated Sinhala word's attested Swa-
Bhasha romanization (the same false-negative risk documented above) —
the eka-construction count recovers them.

Run:  python scripts/measure_codemix_rate.py
Writes data/lexicon/codemix_reference_stats.json:
  measured_rates: {corpus_name: {n_lines, n_tokens, line_rate, token_rate}}
  candidate_english_vocabulary: [{token, count, in_loanword_table}, ...]
    sorted by total attested count, descending
  eka_construction_vocabulary: [{token, count}, ...] — English words
    observed directly attached to a Sinhala "එක" case particle in SOLD
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402
from src.romanizers.aksharamukha import _LOANWORD_OVERRIDES  # noqa: E402

DATA_DIR = REPO_ROOT / "data"
REFERENCE_PATH = DATA_DIR / "reference" / "reference_singlish.txt"
SOLD_DIR = DATA_DIR / "sold"
RAW_WORDS_PATH = DATA_DIR / "raw" / "swabhasha_words.csv"
LEXICON_DIR = DATA_DIR / "lexicon"
OUTPUT_PATH = LEXICON_DIR / "codemix_reference_stats.json"

_TOKEN_RE = re.compile(r"[A-Za-z]+")
MIN_TOKEN_LEN = 2

# Known-genuine English (already hand-verified for the loanword table),
# lowercased once here so it's directly comparable to extracted tokens.
_KNOWN_ENGLISH = {v.lower() for v in _LOANWORD_OVERRIDES.values()}

# --- SOLD scrape-artifact cleaning ---
# Twitter's quoted-tweet embed leaves a header of the form
# "<Display Name tokens> @USER  ·  <D Mon YYYY>" inline in the post text.
# None of that is authored by the poster, so it must not count as
# code-mixing. Matched and stripped (including the date) BEFORE the bare
# @USER/URL placeholders are stripped, since the header pattern needs
# "@USER" as an anchor.
_MONTHS = r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec"
_QUOTED_HEADER_RE = re.compile(
    rf"(?:[A-Za-z]+\s+){{1,4}}@USER\s*·\s*\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}"
)
# Fallback: a bare date not caught above (defensive; rare once the header
# pattern above has run).
_BARE_DATE_RE = re.compile(rf"\b\d{{1,2}}\s+(?:{_MONTHS})\s+\d{{4}}\b")
_PLACEHOLDER_RE = re.compile(r"@USER|URL")
_HASHTAG_RE = re.compile(r"#\w+")
_DOMAIN_RE = re.compile(r"\b[\w-]+\.(?:com|lk|net|org|co)\b", re.I)
# The "eka" construction: an English stem immediately followed by "එක"
# plus an optional case suffix (ට dative, ේ locative, ෙන් instrumental/
# ablative, ක් indefinite). Matched on RAW (uncleaned) text deliberately —
# this is a targeted, self-validating pattern (an English word attached to
# a Sinhala case particle can't be scrape boilerplate), so it doesn't need
# the same artifact-stripping the general rate measurement does.
_EKA_CONSTRUCTION_RE = re.compile(r"([A-Za-z]{3,})\s+එක[කටේෙන්]{0,3}")
# Facebook's cross-posted "feeling <mood>" status-UI text (em dash or
# double-hyphen prefix), e.g. "— feeling crazy" — platform chrome, not
# authored by the poster.
_FEELING_STATUS_RE = re.compile(r"[—-]{1,2}\s*feeling\s+\w+", re.I)
_UI_BOILERPLATE = (
    "Show this thread",
    "Sensitive content",
    "The following media includes potentially sensitive content. Change settings View",
    "This Tweet is unavailable.",
)


def log(msg: str) -> None:
    print(f"[measure_codemix_rate] {msg}")


def clean_sold_text(text: str) -> str:
    """Strip Twitter-scrape artifacts that are not authored code-mixing."""
    for phrase in _UI_BOILERPLATE:
        text = text.replace(phrase, " ")
    text = _FEELING_STATUS_RE.sub(" ", text)
    text = _QUOTED_HEADER_RE.sub(" ", text)
    text = _BARE_DATE_RE.sub(" ", text)
    text = _PLACEHOLDER_RE.sub(" ", text)
    text = _HASHTAG_RE.sub(" ", text)
    text = _DOMAIN_RE.sub(" ", text)
    return text


def latin_tokens(text: str) -> list[str]:
    """Lowercased alphabetic Latin-script tokens, length >= MIN_TOKEN_LEN,
    extracted from the non-Sinhala runs of `text` (so digits/punctuation
    inside a Sinhala-adjacent run never get pulled in)."""
    out = []
    for is_sinhala, run in text_runs(text):
        if is_sinhala:
            continue
        for m in _TOKEN_RE.finditer(run):
            tok = m.group(0).lower()
            if len(tok) >= MIN_TOKEN_LEN:
                out.append(tok)
    return out


def build_attested_sinhala_set() -> set[str]:
    """Every romanized spelling Swa-Bhasha attests for some real Sinhala
    word, lowercased. The negative filter described in the module docstring."""
    attested: set[str] = set()
    n_rows = 0
    with RAW_WORDS_PATH.open("r", encoding="utf-8") as f:
        next(f)  # header
        for line in f:
            line = line.rstrip("\n").rstrip("\r")
            if not line:
                continue
            parts = line.split(",", 1)
            if len(parts) != 2:
                continue
            n_rows += 1
            romanized = parts[0].strip().lower()
            if romanized:
                attested.add(romanized)
    log(f"attested-Sinhala-romanization set: {len(attested)} distinct spellings from {n_rows} raw rows")
    return attested


def sanity_check(attested: set[str]) -> None:
    """A handful of common romanized-Sinhala function words that MUST be in
    the attested set, or the negative filter is silently broken."""
    probes = ["eka", "mata", "hari", "wage", "nam", "mama", "oya"]
    missing = [p for p in probes if p not in attested]
    if missing:
        log(f"WARNING: sanity probes NOT found in attested set: {missing} "
            f"(negative filter may be leaking these into English candidates)")
    else:
        log(f"sanity check passed: all {len(probes)} known Singlish function words are in the attested set")


def is_english(tok: str, attested: set[str]) -> bool:
    return tok in _KNOWN_ENGLISH or tok not in attested


def classify(tokens: list[str], attested: set[str]) -> Counter:
    """{candidate_english_token: count} for tokens not in the attested set,
    plus tokens known-English via the loanword table regardless of the filter."""
    counts: Counter = Counter()
    for tok in tokens:
        if is_english(tok, attested):
            counts[tok] += 1
    return counts


def latin_only_corpus_rates(lines_tokens: list[list[str]], attested: set[str]) -> dict:
    """For an ALREADY all-Latin-script corpus (reference_singlish.txt): every
    token is either a romanized-Sinhala word or an English insertion, so the
    total token count IS the total word-slot count — no separate script to
    account for."""
    n_lines = len(lines_tokens)
    n_tokens = sum(len(toks) for toks in lines_tokens)
    n_english_tokens = 0
    n_lines_with_english = 0
    for toks in lines_tokens:
        english_here = sum(1 for t in toks if is_english(t, attested))
        n_english_tokens += english_here
        if english_here:
            n_lines_with_english += 1
    return {
        "n_lines": n_lines,
        "n_total_word_tokens": n_tokens,
        "n_english_tokens": n_english_tokens,
        "line_rate": (n_lines_with_english / n_lines) if n_lines else 0.0,
        "token_rate": (n_english_tokens / n_tokens) if n_tokens else 0.0,
    }


def mixed_script_corpus_rates(texts: list[str], attested: set[str]) -> dict:
    """For SOLD (Sinhala-script text with Latin-script residue): the
    comparable "word slot" count is Sinhala-script runs (one per Sinhala
    word, via text_runs) PLUS candidate-English Latin tokens — NOT total
    Latin tokens alone, which would wrongly use only the rare Latin residue
    as the denominator instead of the whole post. This makes token_rate
    here directly comparable to latin_only_corpus_rates' token_rate: both
    are "English tokens / total word-slot tokens"."""
    n_lines = len(texts)
    n_sinhala_tokens = 0
    n_english_tokens = 0
    n_lines_with_english = 0
    for text in texts:
        sinhala_count = 0
        english_count = 0
        for is_sinhala_run, run in text_runs(text):
            if is_sinhala_run:
                sinhala_count += 1
                continue
            for m in _TOKEN_RE.finditer(run):
                tok = m.group(0).lower()
                if len(tok) >= MIN_TOKEN_LEN and is_english(tok, attested):
                    english_count += 1
        n_sinhala_tokens += sinhala_count
        n_english_tokens += english_count
        if english_count:
            n_lines_with_english += 1
    n_total = n_sinhala_tokens + n_english_tokens
    return {
        "n_lines": n_lines,
        "n_sinhala_tokens": n_sinhala_tokens,
        "n_english_tokens": n_english_tokens,
        "n_total_word_tokens": n_total,
        "line_rate": (n_lines_with_english / n_lines) if n_lines else 0.0,
        "token_rate": (n_english_tokens / n_total) if n_total else 0.0,
    }


def main() -> None:
    LEXICON_DIR.mkdir(parents=True, exist_ok=True)

    attested = build_attested_sinhala_set()
    sanity_check(attested)

    # --- reference_singlish.txt: already all-Latin, no cleaning needed ---
    ref_lines = [
        line.strip() for line in REFERENCE_PATH.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    ref_tokens_per_line = [
        [m.group(0).lower() for m in _TOKEN_RE.finditer(line) if len(m.group(0)) >= MIN_TOKEN_LEN]
        for line in ref_lines
    ]
    ref_rates = latin_only_corpus_rates(ref_tokens_per_line, attested)
    log(f"reference_singlish.txt: {ref_rates}")

    # --- SOLD: raw vs. cleaned, both splits pooled for the vocabulary,
    # reported separately for the rate so the cleaning's effect is visible.
    # Uses mixed_script_corpus_rates (denominator = Sinhala tokens + English
    # tokens), NOT latin_only, since most of a SOLD post is Sinhala script —
    # counting only the rare Latin residue as the denominator would inflate
    # the rate roughly 5x (measured: 0.68 vs the correct ~0.14). ---
    all_results = {"reference_singlish": ref_rates}
    vocab_counts: Counter = Counter()
    for tok, c in classify([t for toks in ref_tokens_per_line for t in toks], attested).items():
        vocab_counts[tok] += c

    for split in ("train", "test"):
        rows = [json.loads(line) for line in (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8") if line.strip()]
        raw_texts = [r["text"] for r in rows]
        cleaned_texts = [clean_sold_text(r["text"]) for r in rows]

        all_results[f"sold_{split}_raw"] = mixed_script_corpus_rates(raw_texts, attested)
        all_results[f"sold_{split}_cleaned"] = mixed_script_corpus_rates(cleaned_texts, attested)
        log(f"sold_{split} raw:     {all_results[f'sold_{split}_raw']}")
        log(f"sold_{split} cleaned: {all_results[f'sold_{split}_cleaned']}")

        cleaned_latin_tokens = [tok for text in cleaned_texts for tok in latin_tokens(text)]
        for tok, c in classify(cleaned_latin_tokens, attested).items():
            vocab_counts[tok] += c

    vocabulary = [
        {"token": tok, "count": count, "in_loanword_table": tok in _KNOWN_ENGLISH}
        for tok, count in vocab_counts.most_common()
    ]

    # --- eka-construction vocabulary: scanned over RAW SOLD text (both
    # splits), since the pattern itself is self-validating (see docstring) ---
    eka_counts: Counter = Counter()
    for split in ("train", "test"):
        for line in (SOLD_DIR / f"{split}.jsonl").open(encoding="utf-8"):
            if not line.strip():
                continue
            text = json.loads(line)["text"]
            for m in _EKA_CONSTRUCTION_RE.finditer(text):
                eka_counts[m.group(1).lower()] += 1
    eka_vocabulary = [{"token": tok, "count": count} for tok, count in eka_counts.most_common()]
    log(f"eka-construction vocabulary: {len(eka_vocabulary)} distinct English stems, "
        f"{sum(eka_counts.values())} total occurrences")

    output = {
        "measured_rates": all_results,
        "candidate_english_vocabulary": vocabulary,
        "n_candidate_tokens": len(vocabulary),
        "eka_construction_vocabulary": eka_vocabulary,
        "methodology_note": (
            "candidate English tokens = Latin-script tokens NOT attested as any "
            "Sinhala word's romanization in data/raw/swabhasha_words.csv, unioned "
            "with the already-verified 123-entry loanword table. SOLD rates are "
            "reported both raw and after stripping Twitter-scrape artifacts "
            "(quoted-tweet headers, @USER/URL placeholders, hashtags, domains). "
            "Every candidate here still requires hand verification before use — "
            "see scripts/build_codemix_lexicon.py. eka_construction_vocabulary is "
            "a second, stronger channel: English stems observed directly attached "
            "to a Sinhala 'එක' case particle in SOLD's own raw text — the exact "
            "construction the noiser produces, so it recovers words the Latin-token "
            "filter above missed via a coincidental Swa-Bhasha collision."
        ),
    }
    OUTPUT_PATH.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    log(f"wrote {len(vocabulary)} candidate tokens -> {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
