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
| 3 | Code-mixing noise vector | Not started |
| 4 | Misspelling / abbreviation noise vectors | Not started |
| 5 | Full dataset generation | Not started |

**Headline results** (`python eval/harness.py`, full 10,000-post corpus):
- `gold_cer` (aksharamukha, colloquial scheme) = **0.039** against a
  target of < 0.10, the best of five backends compared, including the
  actual live UoM Sinhala Romaniser website.
- `realism_jsd` (transliteration, light/heavy severity) = **0.105 / 0.107**
  against a target of 0.076 (30% reduction from baseline) — **target not
  met**, recorded as-is rather than adjusted to look better. See
  `docs/research_documentation.md` §7–8 for the full discussion.
- All 13 invariants and 8 regression cases pass.

See `docs/research_documentation.md` for the complete methodology,
data-source provenance, and results writeup.

## Quickstart

```bash
python -m venv .venv
.venv/Scripts/activate        # or: source .venv/bin/activate
pip install -r requirements.txt

python scripts/fetch_data.py              # fetch SOLD + Swa-Bhasha, build gold/reference sets
python eval/harness.py                     # run the full evaluation suite -> eval/report.json
python scripts/build_word_variants.py      # build the spelling-variant lexicon
python scripts/generate_transliteration.py # generate the noised dataset
python scripts/build_review_sample.py      # build a 100-item sample for manual review
```

## Repository layout

```
data/
  sold/          SOLD train/test, parsed to JSONL (never edited)
  gold/          Sinhala<->Romanized pairs held out for CER scoring
  reference/     real Singlish text used for realism scoring
  lexicon/       attested spelling-variant lookup (built by build_word_variants.py)
  outputs/       generated noised sets + the human-review sample
src/
  graphemes.py       grapheme-cluster utilities (Sinhala syllables are multi-codepoint)
  schema.py          output row schema + validation
  pipeline.py         compound noising pipeline
  romanizers/        Sinhala -> Singlish backends (aksharamukha, UoM-rules reimplementation, etc.)
  noisers/           transliteration.py (done), codemix/misspell/abbreviate (stubs)
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
