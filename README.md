# Sinhala Noise Dataset Builder

A pipeline that transforms [SOLD](https://huggingface.co/datasets/sinhala-nlp/SOLD)
(the Sinhala Offensive Language Dataset) into "noised" variants — text
rendered the way people actually type Sinhala online: romanized
("Singlish"), code-mixed with English, misspelled, and abbreviated — at
two severity levels each, for benchmarking hate-speech detection models
under realistic input noise.

**Design principle:** the evaluation harness (`eval/harness.py`) was built
*before* any noise-generation code. Every subsequent design decision was
accepted or rejected by whether it improved the harness's measured
output — CER against a gold romanization set, realism divergence against
real Singlish text, and a set of hard pass/fail invariants — not by
inspection alone.

## Status

| Phase | Goal | Status |
|---|---|---|
| 0 | Build the verifier (harness, metrics, gold/reference data) | Complete |
| 1 | Select a Sinhala→Romanized ("Singlish") conversion backend | Complete |
| 2 | Build the transliteration noiser; generate real output | Complete, paused at manual review |
| 3 | Code-mixing noise vector | Complete — human-review gate closed |
| 4a | Misspelling noise vector | Complete — human-review gate closed |
| 4b | Abbreviation noise vector | Complete — human-review gate closed |
| 5 | Compound pipeline, full dataset generation, GATE B | Not started |

**Headline results** (`python eval/harness.py`, full 10,000-post corpus):
- `gold_cer` (aksharamukha, colloquial scheme) = **0.039** against a
  target of < 0.10, the best of five backends compared, including the
  actual live UoM Sinhala Romaniser website.
- `realism_jsd` (transliteration, light/heavy severity) = **0.105 / 0.107**
  against a target of 0.076 (30% reduction from baseline) — **target not
  met**, recorded as-is rather than adjusted to look better. See
  `docs/research_documentation.md` §7–8 for the full discussion.
- `codemix`: **93.2% / 93.9%** of posts (train/test) touched by a real
  substitution, up from an earlier probabilistic design's 14-20% — see
  `docs/research_documentation.md` §9 for the full v1→v2 redesign and the
  3-round human review that followed it.
- `misspell`: Sinhala IME-collision confusion sets (§11), 90% cluster-token
  coverage, approved as-is in a single human-review round.
- `abbreviate`: phrase-initialism lexicon (§13), 378 human-approved
  bigrams, opt-in review (nothing ships without explicit approval) —
  started as a two-channel design, one channel (word clipping) was
  dropped entirely after user review judged it "total garbage."
- All 16 invariants and 21 regression cases pass.

See `docs/research_documentation.md` for the complete methodology,
data-source provenance, and results writeup.

## Quickstart

```bash
python -m venv .venv
.venv/Scripts/activate        # or: source .venv/bin/activate
pip install -r requirements.txt

python scripts/fetch_data.py              # fetch SOLD + Swa-Bhasha, build gold/reference sets
python eval/harness.py                     # run the full evaluation suite -> eval/report.json

# transliteration
python scripts/build_word_variants.py      # build the spelling-variant lexicon
python scripts/generate_transliteration.py # generate the noised dataset
python scripts/build_review_sample.py --condition transliteration

# code-mixing (word bank already built; these scripts rebuild it from source)
python scripts/select_codemix_targets.py       # candidate words per post -> translation worklist
python scripts/translate_codemix_worklist.py --submit   # one-time LLM batch translation
python scripts/build_codemix_wordbank.py       # merge verified + LLM + human-review-corrections -> frozen word bank
python scripts/generate_codemix.py             # generate the noised dataset
python scripts/build_codemix_usage_report.py   # impact-ordered review report
python scripts/build_review_sample.py --condition codemix

# misspelling (confusion sets already built; rebuilds from source)
python scripts/build_misspell_confusions.py    # derive IME-collision confusion sets + attestation vocab
python scripts/generate_misspell.py            # generate the noised dataset
python scripts/build_review_sample.py --condition misspell

# abbreviation (initialism lexicon already built; rebuilds from source)
python scripts/build_abbreviate_initialisms.py # mine candidate bigrams + merge review approvals -> frozen lexicon
python scripts/generate_abbreviate.py          # generate the noised dataset
python scripts/build_review_sample.py --condition abbreviate
```

## Repository layout

```
data/
  sold/          SOLD train/test, parsed to JSONL (never edited)
  gold/          Sinhala<->Romanized pairs held out for CER scoring
  reference/     real Singlish text used for realism scoring
  lexicon/       word_variants.jsonl (spelling variants, transliteration);
                 codemix_wordbank.jsonl (frozen, code-mixing — merged from
                 the hand-curated lexicon, LLM translation, and 3 rounds of
                 human review corrections; see docs §9);
                 misspell_confusions.jsonl (frozen, IME-collision confusion
                 sets; see docs §11); abbreviate_initialisms.jsonl (frozen,
                 378 human-approved phrase-initialism bigrams, opt-in
                 review; see docs §13)
  outputs/       generated noised sets + human-review samples
src/
  graphemes.py       grapheme-cluster utilities (Sinhala syllables are multi-codepoint)
  schema.py          output row schema + validation
  pipeline.py         compound noising pipeline (stub — not yet built)
  romanizers/        Sinhala -> Singlish backends (aksharamukha, UoM-rules reimplementation, etc.)
  noisers/           transliteration.py, codemix.py, misspell.py, abbreviate.py — all four vectors done
eval/
  harness.py         runs everything, writes eval/report.json + report.md
  invariants.py       hard pass/fail checks
  gold_cer.py         CER vs. the gold set
  realism.py          char-3-gram JSD vs. a real-Singlish reference corpus
  regression/         frozen hand-checked cases that must keep passing
scripts/              one-off / generation scripts (see docstrings for what each does)
docs/research_documentation.md   full methodology + results writeup
```

## Data sources

- **SOLD** — `sinhala-nlp/SOLD` on HuggingFace: 10,000 Sinhala social-media
  posts labeled offensive/not-offensive. Fetched directly over HTTP by
  `scripts/fetch_data.py`; exact file hashes recorded in
  `data/PROVENANCE.json`.
- **Swa-Bhasha** — a Sinhala-romanization word/sentence corpus, used to
  build the CER gold set, the realism reference corpus, and the
  spelling-variant lexicon.
- **UoM Sinhala Romaniser** (https://nisansads.staff.uom.lk/CodeSamples/sinhala_romaniser.php)
  — a live third-party tool used as one comparison backend in the
  romanizer bake-off; called only twice, ever, to build small cached
  calibration/comparison samples (never in a loop — see
  `src/romanizers/uom_rules.py`).

Full provenance and methodology for all of the above are in
`docs/research_documentation.md` §2.

## License

The code in this repository is MIT-licensed (see `LICENSE`). This does
**not** extend to the contents of `data/` — SOLD, Swa-Bhasha, and the UoM
Sinhala Romaniser's output are third-party data, included here for
research reproducibility, and remain under whatever terms their original
authors/publishers set.

## Requirements

Python 3.11+. See `requirements.txt`.
