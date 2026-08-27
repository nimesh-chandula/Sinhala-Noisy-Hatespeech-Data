"""
Code-Mixing Index (CMI) and switch-frequency metrics — the standard,
literature-anchored replacement for this project's in-house
`realised_noise_rate` (see src/noisers/codemix.py's "Round 5" docstring
section and the plan for the full justification).

Three metrics, all computed from the same underlying S/E token sequence:

  CMI  (Das & Gambäck 2014; Gambäck & Das 2016)
       100 * (1 - max(w_i) / (n - u)), where n is total tokens, u is
       language-independent tokens (already excluded here by construction
       — see `token_sequence` below — rather than subtracted after the
       fact), and max(w_i) is the token count of the dominant language.
       0 = monolingual. Reported per POST, then aggregated (mean + the
       6-band histogram convention this repo uses throughout, see
       measure_codemix_rate.py's existing bands).

  SPF  (Pratapa et al. 2018) — switch-point fraction: the count of
       adjacent-token language changes, divided by (n-1). 0 = no switching
       (one contiguous block per language), 1 = alternates every token.

  I-index (Guzmán et al. 2017) — same switch-counting idea, normalized by
       n instead of (n-1) (the convention this module uses to keep it
       numerically distinct from SPF rather than a duplicate of it; both
       measure switching frequency/"burstiness", not overall language
       balance — this module does not implement Guzmán's separate
       M-index, which measures balance, not switching).

--- Why token classification is NOT reused as-is from the noiser's own logic ---
For a fair CMI comparison between generated codemix output and SOLD's
natural rate, both sides must be classified with the SAME rule: a token is
Sinhala-script (S) or Latin-script (E) after stripping Twitter-scrape
artifacts. This module intentionally reuses the EXACT classification and
cleaning already validated in scripts/measure_codemix_rate.py (the
Swa-Bhasha negative-filter LID + _LOANWORD_OVERRIDES + clean_sold_text's
artifact stripping) rather than inventing a second, simpler Latin-vs-
Sinhala split for generated output — an apples-to-apples comparison is the
entire point of measuring a reference distribution at all.

--- Why this can be unavailable ---
scripts/measure_codemix_rate.py imports src.romanizers.aksharamukha for
its loanword table, which requires the `aksharamukha` package — not
installed in every interpreter (see eval/harness.py's existing
_NOISERS_UNAVAILABLE pattern for gold_cer/realism/noise_rate_error, all of
which already handle this). This module follows the same "loud on purpose"
discipline: unavailability is reported, never silently swallowed into a
misleadingly-empty result.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.graphemes import text_runs  # noqa: E402

# CMI histogram bands, matching the convention already established in
# data/lexicon/codemix_reference_stats.json / this repo's write-ups.
CMI_BANDS = [(0, 10), (11, 20), (21, 30), (31, 40), (41, 50), (51, 1000)]
CMI_BAND_LABELS = ["0-10", "11-20", "21-30", "31-40", "41-50", "50+"]

_measure_module = None
_UNAVAILABLE_REASON: str | None = None


def _load_measure_module():
    """Lazily import scripts/measure_codemix_rate.py by file path (scripts/
    is not a package, mirroring how _codemix_common.py's sibling scripts
    are loaded elsewhere in this repo). Cached; returns None on failure,
    setting _UNAVAILABLE_REASON so callers can report why."""
    global _measure_module, _UNAVAILABLE_REASON
    if _measure_module is not None:
        return _measure_module
    if _UNAVAILABLE_REASON is not None:
        return None
    try:
        spec = importlib.util.spec_from_file_location(
            "_measure_codemix_rate_for_cmi", REPO_ROOT / "scripts" / "measure_codemix_rate.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _measure_module = module
        return module
    except ImportError as e:
        _UNAVAILABLE_REASON = str(e)
        return None


def is_available() -> bool:
    return _load_measure_module() is not None


def unavailable_reason() -> str | None:
    _load_measure_module()
    return _UNAVAILABLE_REASON


def token_sequence_script_only(text: str) -> list[str]:
    """('S' | 'E') per token, classified PURELY by script (Sinhala vs Latin)
    after the same clean_sold_text artifact-stripping token_sequence()
    uses -- no Swa-Bhasha LID filter.

    --- Why this exists as a SEPARATE function, not a flag on token_sequence ---
    Discovered empirically while sanity-checking round 5's generated codemix
    output: 58% of a random sample of codemix_wordbank.jsonl's own English
    headwords ("old", "set", "class", ...) coincidentally collide with SOME
    real Sinhala word's romanized spelling somewhere in the 5.9-million-entry
    Swa-Bhasha table token_sequence()'s LID filter treats as "known Sinhala,
    not English." That filter is CORRECT for measuring natural SOLD text,
    where genuine ambiguity exists (a Latin token really could be romanized
    Sinhala). It is WRONG for measuring this noiser's OWN output: codemix
    runs before transliteration in every pipeline (standalone and compound
    -- see src/pipeline.py), so a Latin-script run in codemix's noisy_text
    is unambiguously either (a) pre-existing English/placeholder content
    inherited verbatim from the original SOLD post, or (b) this noiser's own
    genuine-English substitution -- never romanized Sinhala, because nothing
    has romanized anything yet at this pipeline stage. Applying the natural-
    text LID filter to generated output was measuring ~half the real CMI
    (mean 10.0 vs the noiser's own internal budget accounting of ~14.9 on
    the same generated rows) purely from this collision artifact, not from
    any real generation defect. Use THIS function for codemix's own
    generated output; use token_sequence() (with the LID filter) only for
    genuinely ambiguous text -- SOLD's natural corpus, or any post-
    transliteration (compound) text where script no longer reliably signals
    language at all (see corpus_cmi_stats's compound/transliteration
    not_applicable handling)."""
    m = _load_measure_module()
    cleaned = m.clean_sold_text(text)
    seq: list[str] = []
    for is_sinhala, run in text_runs(cleaned):
        if is_sinhala:
            seq.append("S")
        else:
            for match in m._TOKEN_RE.finditer(run):
                if len(match.group(0)) >= m.MIN_TOKEN_LEN:
                    seq.append("E")
    return seq


def token_sequence(text: str, attested: set[str]) -> list[str]:
    """('S' | 'E') per token, after clean_sold_text strips scrape artifacts
    (quoted-tweet headers, @USER/URL placeholders, hashtags, domains — see
    measure_codemix_rate.py's module docstring) and Sinhala runs are
    counted one-token-per-run (== one word, matching how the noiser itself
    counts substitution units). u (language-independent tokens: punctuation,
    digits, emoji) is never appended to the sequence at all, rather than
    added then subtracted — _TOKEN_RE only matches ASCII letters and
    text_runs only yields Sinhala-vs-other runs, so both are excluded by
    construction, satisfying CMI's `n - u` denominator directly."""
    m = _load_measure_module()
    cleaned = m.clean_sold_text(text)
    seq: list[str] = []
    for is_sinhala, run in text_runs(cleaned):
        if is_sinhala:
            seq.append("S")
        else:
            for match in m._TOKEN_RE.finditer(run):
                tok = match.group(0).lower()
                if len(tok) >= m.MIN_TOKEN_LEN:
                    seq.append("E" if m.is_english(tok, attested) else "S")
    return seq


def build_attested_set() -> set[str]:
    m = _load_measure_module()
    return m.build_attested_sinhala_set()


def compute_cmi(seq: list[str]) -> float | None:
    """100 * (1 - max(w_i)/n) over a 2-language {S, E} sequence. None if the
    sequence is empty (undefined, not zero — a post with zero word-slot
    tokens says nothing about mixing)."""
    n = len(seq)
    if n == 0:
        return None
    n_e = seq.count("E")
    n_s = n - n_e
    return 100.0 * (1.0 - max(n_e, n_s) / n)


def compute_spf(seq: list[str]) -> float | None:
    """Switch-point fraction: adjacent-token language changes / (n-1).
    None if n < 2 (no adjacency to measure)."""
    n = len(seq)
    if n < 2:
        return None
    switches = sum(1 for i in range(1, n) if seq[i] != seq[i - 1])
    return switches / (n - 1)


def compute_i_index(seq: list[str]) -> float | None:
    """Guzmán et al. (2017)-style switching frequency, normalized by n
    rather than SPF's (n-1) — see module docstring for why the two are kept
    numerically distinct. None if n < 2."""
    n = len(seq)
    if n < 2:
        return None
    switches = sum(1 for i in range(1, n) if seq[i] != seq[i - 1])
    return switches / n


def cmi_band(cmi: float) -> str:
    for (lo, hi), label in zip(CMI_BANDS, CMI_BAND_LABELS):
        if lo <= cmi <= hi:
            return label
    return CMI_BAND_LABELS[-1]


def corpus_cmi_stats(texts: list[str], attested: set[str] | None = None, *, only_mixed: bool = True,
                      script_only: bool = False) -> dict:
    """Aggregate CMI/SPF/I-index stats over a list of raw texts.

    Band shares and SPF/I-index are ALWAYS computed over posts with CMI > 0
    only (switching frequency is undefined for a monolingual post, and a
    band histogram of "0" values isn't a shape) — matching the convention
    already established in data/lexicon/codemix_reference_stats.json.

    only_mixed controls `cmi_mean`/`cmi_median` specifically: True (default,
    the reporting convention used throughout this repo's write-ups) means
    those two are ALSO computed over mixed posts only, since a corpus-wide
    mean dominated by monolingual posts (86.6% of SOLD) would obscure the
    shape of the mixing that does happen. False computes them over ALL
    posts (cmi=0 included) instead — the POPULATION mean, needed when
    comparing against a target that already has its own zero-mass baked in
    (e.g. eval/invariants.py's check_codemix_cmi_distribution, comparing
    against a band-implied mean computed over the full declared
    distribution, zeros included). `line_rate` (fraction of ALL posts that
    are mixed at all) is reported unconditionally either way, so nothing
    about the unmixed majority is ever hidden regardless of this flag.

    script_only=True switches to token_sequence_script_only (no LID filter,
    no `attested` set needed) -- use this for measuring THIS PROJECT'S OWN
    generated codemix output, never for natural/ambiguous text. See
    token_sequence_script_only's docstring for why the two must not be
    conflated.
    """
    n_total = 0
    n_mixed = 0
    all_cmis: list[float] = []
    mixed_cmis: list[float] = []
    spfs: list[float] = []
    i_indices: list[float] = []
    for text in texts:
        seq = token_sequence_script_only(text) if script_only else token_sequence(text, attested)
        cmi = compute_cmi(seq)
        if cmi is None:
            continue
        n_total += 1
        all_cmis.append(cmi)
        if cmi > 0:
            n_mixed += 1
            mixed_cmis.append(cmi)
            spf = compute_spf(seq)
            if spf is not None:
                spfs.append(spf)
            i_idx = compute_i_index(seq)
            if i_idx is not None:
                i_indices.append(i_idx)

    band_counts = {label: 0 for label in CMI_BAND_LABELS}
    for cmi in mixed_cmis:
        band_counts[cmi_band(cmi)] += 1

    def _mean(xs: list[float]) -> float | None:
        return sum(xs) / len(xs) if xs else None

    def _median(xs: list[float]) -> float | None:
        if not xs:
            return None
        s = sorted(xs)
        return s[len(s) // 2]

    cmi_pool = mixed_cmis if only_mixed else all_cmis
    return {
        "n_posts": n_total,
        "n_mixed": n_mixed,
        "line_rate": (n_mixed / n_total) if n_total else 0.0,
        "cmi_mean": _mean(cmi_pool),
        "cmi_median": _median(cmi_pool),
        "cmi_band_counts": band_counts,
        "cmi_band_shares": {k: (v / n_mixed if n_mixed else 0.0) for k, v in band_counts.items()},
        "spf_mean": _mean(spfs),
        "spf_median": _median(spfs),
        "i_index_mean": _mean(i_indices),
    }
