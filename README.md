# ArabicMedReason

A small, systematic evaluation benchmark for testing whether a small open-weight
language model reasons about clinical scenarios consistently in Arabic and English,
or whether it relies on surface-level medical associations.

> **Status**
> - **Pilot (completed run, immutable):** 10 Arabic items (`data/pilot.csv`) were run once with
>   `Qwen/Qwen3.5-4B` to debug the evaluation pipeline. The raw outputs are stored unchanged in
>   `results/raw_outputs.jsonl` and `results/run_config.json`. They have not been scored, and no
>   findings are reported from them.
> - **Full evaluation (dataset ready, not yet run):** 100 matched Arabic/English items
>   (`data/evaluation.csv`). **No full-evaluation results exist yet.** Nothing in this repository
>   should be read as a finding about any model or language until that run is performed and analysed.
> - All cases are **synthetic** and contain no real patient information. They are draft benchmark
>   items that still require human expert review.

## Motivation

Language models are increasingly used for medical question answering, and most
evaluation is done in English. Strong scores on knowledge-recall benchmarks do not
show whether a model actually reasons over the evidence in a case. A model could
answer correctly by matching familiar patterns ("new drug + rash → drug reaction")
without checking whether the evidence supports that conclusion.

It is also an open question whether reasoning behaviour carries over across languages.
This project tests that question with controlled items. It does not assume an answer.

## Research question

> Do small open-weight language models perform clinical reasoning consistently in
> Arabic compared with English, particularly when small changes in clinical evidence
> should change the correct conclusion?

Hypotheses to test (none confirmed or rejected yet):

1. **Evidence sensitivity:** when one decisive fact in a case changes, the model's
   answer changes accordingly.
2. **Cross-lingual consistency:** model accuracy and pair-level consistency are
   similar for matched Arabic and English items.
3. **Category dependence:** any differences vary by reasoning category.

## Pilot vs. full evaluation

| | Pilot | Full evaluation |
|---|---|---|
| File | `data/pilot.csv` | `data/evaluation.csv` |
| Purpose | Debug the pipeline and the item format | Main controlled comparison |
| Languages | Arabic only | Arabic + matched English |
| Minimal pairs | 5 (1 per category) | 25 (5 per category) |
| Rows | 10 | 100 (50 Arabic + 50 English) |
| Gold rationale / flip metadata | No | Yes (`expected_reason`, `evidence_flip`) |
| Raw outputs | `results/raw_outputs.jsonl` | `results/evaluation_raw_outputs.jsonl` (after the run) |
| Run config | `results/run_config.json` | `results/evaluation_run_config.json` (after the run) |

The pilot files are kept as an immutable first experiment and are never overwritten. The
full-evaluation cases were written from scratch; they do not reuse the pilot items.

## Full evaluation design

- **25 minimal pairs × 2 variants (A/B) × 2 languages = 100 rows.**
- **5 pairs per reasoning category**, 5 categories.
- **Scenarios:** 50 distinct synthetic Arabic scenarios, each with exactly one English counterpart
  sharing the same `scenario_id`.

### Controlled minimal pairs

Within each pair, the A and B cases are identical except for **one decisive piece of evidence**
(e.g. a date, a time, a single word such as left/right, or one record entry). That change flips
the correct answer. The question is identical for A and B, so only the case evidence differs.
A model that answers both variants correctly is responding to the evidence. A model that gives
the same answer to both is not.

Design controls:

- **No external knowledge needed.** Any rule needed to answer (a protocol, a fever threshold,
  the items a label must show) is stated inside the case.
- **Objectively gradeable answers.** Binary questions use fixed labels (`Yes` / `No`,
  `نعم` / `لا`). False-premise items expect an explicit rejection of the premise, or a short
  entity when the premise holds.
- **Counterbalancing.** Within each binary category, 5 expected answers are Yes and 5 are No.
  The A variant is not tied to one answer: across the 20 binary pairs, A is "Yes" in 10 and "No"
  in 10, with no fixed position pattern. For contradiction and missing-evidence pairs this is
  achieved by alternating the question's polarity (e.g. "contradict?" vs. "consistent?").
  For false-premise pairs, A is always the variant whose premise is unsupported, as specified
  in the design.
- **Language matching.** Arabic (Modern Standard Arabic) and English rows are semantically
  equivalent: same evidence, same flip, same expected answer.

### Data schema (`data/evaluation.csv`)

| Column | Description | Shown to the model? |
|---|---|---|
| `id` | Unique row id: `AR-TMP-01A`, `EN-TMP-01A` | No |
| `category` | One of the five reasoning categories | No |
| `language` | `ar` or `en` | No |
| `pair_id` | Minimal pair shared by A/B and both languages, e.g. `TMP-01` | No |
| `scenario_id` | Language-independent scenario, e.g. `TMP-01A` (shared by `AR-` and `EN-` rows) | No |
| `case_text` | Synthetic clinical vignette | **Yes** |
| `question` | Question about the vignette | **Yes** |
| `expected_answer` | Short reference answer | No |
| `expected_reason` | Short gold rationale naming the evidence that decides the answer | No |
| `evidence_flip` | The single evidence change between A and B (same text for both languages) | No |

`pilot.csv` uses the original 7-column schema (no `scenario_id`, `expected_reason`, `evidence_flip`).

### Why `expected_reason` and `evidence_flip` exist

Final-answer correctness alone can hide reasoning errors: a model can reach the right label for
the wrong reason. These fields support the later **human** evaluation of reasoning quality:

- `expected_reason` states which evidence in the case determines the answer, so a reviewer can
  check whether the model's stated `REASON` cites that evidence.
- `evidence_flip` documents what differs between A and B, so pair-level behaviour can be
  interpreted against the intended manipulation.

**Both fields are hidden from the model.** The inference notebook builds each prompt from
`case_text` and `question` only (`build_prompt(case_text, question)`). Assertions check that no
reference field or identifier (`expected_answer`, `expected_reason`, `evidence_flip`, `id`,
`pair_id`, `scenario_id`) appears in any prompt. These fields are copied into the output file
next to the raw response only for human review.

## Reasoning categories

| Category | What it tests |
|---|---|
| `temporal_reasoning` | Whether the order of events makes a claimed relationship possible |
| `contradiction_detection` | Whether the model notices conflicting statements in a record |
| `missing_evidence` | Whether the model notices that required information is absent rather than assuming it |
| `false_premise` | Whether the model rejects a question built on an assumption the case does not support |
| `causal_reasoning` | Whether the evidence (e.g., stopping and restarting a drug) supports a causal claim |

## Repository structure

```
ArabicMedReason/
├── README.md
├── requirements.txt              # local, lightweight dependencies only (no PyTorch)
├── data/
│   ├── pilot.csv                 # pilot: 10 Arabic items, 5 minimal pairs (immutable)
│   └── evaluation.csv            # full set: 100 rows, 25 pairs, Arabic + English
├── src/
│   └── validate_dataset.py       # schema / design checks for both datasets
├── notebooks/
│   └── evaluation.ipynb          # Kaggle inference notebook (DATASET = "evaluation" or "pilot")
├── results/
│   ├── raw_outputs.jsonl         # pilot raw outputs (immutable)
│   └── run_config.json           # pilot run configuration (immutable)
└── analysis/
    └── error_analysis.md         # empty analysis template
```

## Setup and validation

```bash
pip install -r requirements.txt
python src/validate_dataset.py                       # validates data/pilot.csv (pilot schema)
python src/validate_dataset.py data/evaluation.csv   # validates the full evaluation design
```

The validator detects the schema from the header. For `evaluation.csv` it also checks:
- the design counts: 100 rows, 50 per language, 25 pairs, 5 pairs per category;
- that each pair has exactly Arabic-A, Arabic-B, English-A and English-B;
- that each scenario has one Arabic and one English row with matching category and pair;
- the consistency of the identifiers;
- that `expected_reason` and `evidence_flip` are not empty;
- that no `case_text` is duplicated.

It exits with a non-zero status if validation fails.

## Running inference (Kaggle)

1. **Settings:** set Accelerator to GPU and turn Internet on.
2. **Get the code:** clone the repo with `!git clone https://github.com/ShahadAlsultan/ArabicMedReason.git`, then `%cd ArabicMedReason`.
3. **Open the notebook:** `notebooks/evaluation.ipynb`, with `DATASET = "evaluation"` (the default).
4. **Run:** run the install cell, restart the kernel, then run the rest.
5. **Collect the outputs:** download `results/evaluation_raw_outputs.jsonl` and `results/evaluation_run_config.json` and commit them.

The notebook keeps the pilot setup unchanged:
- the same fixed prompt template;
- thinking disabled;
- greedy decoding;
- batch size 1;
- the exact raw response saved for every case.

It does not grade answers or use an LLM judge, and it refuses to overwrite existing result files.

## Evaluation plan

1. **Item review:** clinicians and native Arabic speakers review the items for clinical
   plausibility, ambiguity, naturalness and Arabic–English equivalence.
2. **Inference:** run the full evaluation on Kaggle as above.
3. **Scoring (human, rubric-based):** grade each response on
   - final-answer correctness against `expected_answer` (label, entity, or premise rejection);
   - reasoning quality, i.e. whether `REASON` cites the evidence in `expected_reason`.
4. **Metrics:**
   - accuracy overall, by category and by language;
   - minimal-pair consistency (both variants of a pair answered correctly);
   - cross-lingual agreement on matched Arabic/English scenarios.
5. **Error analysis:** fill in `analysis/error_analysis.md` using only real outputs.

With 25 pairs per language, results will be descriptive. Any statistical claim will need to
account for the small sample size.

## Ethics and data

All cases are invented for this benchmark. They do not describe real patients and
contain no personal or identifiable information. The benchmark evaluates model
behaviour and is not intended for clinical use.
