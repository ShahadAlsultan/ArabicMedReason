# ArabicMedReason

A small, systematic evaluation benchmark for testing whether a small open-weight
language model reasons about clinical scenarios consistently in Arabic and English,
or whether it relies on surface-level medical associations.

> **Status: Phase 1 (infrastructure only).**
> - All current cases are **synthetic draft items** written for human review. They are
>   not validated research data and contain no real patient information.
> - **No model has been run. No results exist yet.** Nothing in this repository should
>   be read as a finding about any model or language.

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

## Benchmark design

- **Synthetic, controlled scenarios.** Short cases that need general reasoning, not
  specialist medical knowledge or trivia. Where a clinical rule matters, the case
  states it explicitly.
- **Minimal pairs.** Each pair (`pair_id`) contains two nearly identical cases (`…A`
  and `…B`) that differ in one decisive fact, and that difference changes the correct
  answer. A model that gets one item right and the other wrong, or that gives the same
  answer to both, is not responding to the evidence.
- **Matched languages (planned).** Every Arabic item will get an English counterpart
  with the same structure, so results can be compared item by item across languages.
- **Objectively gradeable answers.** Answers take the form yes/no, a named entity, or
  an explicit rejection of a false premise, each with a short justification.

### Data schema (`data/pilot.csv`)

| Column | Description |
|---|---|
| `id` | Unique item id, e.g. `AR-TMP-01A` (language–category–pair number + variant) |
| `category` | One of the five reasoning categories below |
| `language` | `ar` or `en` |
| `pair_id` | Minimal-pair identifier shared by the A/B variants, e.g. `TMP-01` |
| `case_text` | Synthetic clinical vignette |
| `question` | Question about the vignette |
| `expected_answer` | Reference answer: a short label followed by a brief justification |

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
├── requirements.txt          # local, lightweight dependencies only (no PyTorch)
├── data/
│   └── pilot.csv             # 10 synthetic draft items (Arabic), 5 minimal pairs
├── src/
│   └── validate_dataset.py   # schema / integrity checks for the dataset
├── notebooks/
│   └── evaluation.ipynb      # placeholder; Kaggle inference notebook (Phase 2)
├── results/                  # raw model outputs will go here (currently empty)
└── analysis/
    └── error_analysis.md     # empty analysis template
```

## Setup and validation

```bash
pip install -r requirements.txt
python src/validate_dataset.py            # validates data/pilot.csv
python src/validate_dataset.py other.csv  # or any file with the same schema
```

The script exits with a non-zero status if validation fails.

## Evaluation plan

1. **Item review:** clinicians and native Arabic speakers review the draft items for
   clinical plausibility, ambiguity and linguistic naturalness.
2. **English counterparts:** create matched English items and check that the A/B
   difference is preserved in translation.
3. **Inference (Kaggle GPU):** run a small open-weight model with a fixed prompt
   template and deterministic decoding. Save raw outputs, model version and settings
   to `results/`.
4. **Scoring:** grade answers against `expected_answer` using a documented rubric that
   checks the label (yes/no, entity, or premise rejection).
5. **Metrics:**
   - accuracy overall and by category;
   - minimal-pair consistency (both items in a pair answered correctly);
   - cross-lingual agreement on matched Arabic/English items.
6. **Error analysis:** fill in `analysis/error_analysis.md` using only real outputs.

With the current pilot size (10 items), any result will be descriptive and
exploratory. It will not support statistical claims.

## Ethics and data

All cases are invented for this benchmark. They do not describe real patients and
contain no personal or identifiable information. The benchmark evaluates model
behaviour and is not intended for clinical use.
