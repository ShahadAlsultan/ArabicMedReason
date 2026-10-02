"""Validate the ArabicMedReason benchmark CSV.

Usage:
    python src/validate_dataset.py [path/to/dataset.csv]

Defaults to data/pilot.csv. Exits with status 1 if any error is found.
"""

import sys
from pathlib import Path

import pandas as pd

REQUIRED_COLUMNS = [
    "id",
    "category",
    "language",
    "pair_id",
    "case_text",
    "question",
    "expected_answer",
]
NON_EMPTY_COLUMNS = ["id", "pair_id", "case_text", "question", "expected_answer"]
ALLOWED_CATEGORIES = {
    "temporal_reasoning",
    "contradiction_detection",
    "missing_evidence",
    "false_premise",
    "causal_reasoning",
}
ALLOWED_LANGUAGES = {"ar", "en"}

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "data" / "pilot.csv"


def validate(path: Path) -> tuple[list[str], list[str], pd.DataFrame | None]:
    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return [f"File not found: {path}"], warnings, None

    # Read everything as text and keep empty cells as "" so blanks are detectable.
    df = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    df = df.apply(lambda col: col.str.strip())

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
        return errors, warnings, df

    extra = [c for c in df.columns if c not in REQUIRED_COLUMNS]
    if extra:
        warnings.append(f"Unexpected extra columns: {extra}")

    # Row numbers reported as they appear in the file (header is line 1).
    def rows(mask: pd.Series) -> list[int]:
        return [i + 2 for i in df.index[mask]]

    for col in NON_EMPTY_COLUMNS:
        empty = df[col] == ""
        if empty.any():
            errors.append(f"Empty '{col}' on line(s) {rows(empty)}")

    dup = df["id"].duplicated(keep=False) & (df["id"] != "")
    if dup.any():
        errors.append(f"Duplicate ids: {sorted(df.loc[dup, 'id'].unique())}")

    bad_cat = ~df["category"].isin(ALLOWED_CATEGORIES)
    if bad_cat.any():
        errors.append(
            f"Invalid category on line(s) {rows(bad_cat)}: "
            f"{sorted(df.loc[bad_cat, 'category'].unique())}"
        )

    bad_lang = ~df["language"].isin(ALLOWED_LANGUAGES)
    if bad_lang.any():
        errors.append(
            f"Invalid language on line(s) {rows(bad_lang)}: "
            f"{sorted(df.loc[bad_lang, 'language'].unique())} "
            f"(allowed: {sorted(ALLOWED_LANGUAGES)})"
        )

    # Soft checks on minimal-pair structure (warnings only).
    paired = df[df["pair_id"] != ""]
    for (pid, lang), group in paired.groupby(["pair_id", "language"]):
        pair_id = f"{pid} [{lang}]"
        if len(group) != 2:
            warnings.append(f"pair {pair_id} has {len(group)} item(s), expected 2")
        if group["category"].nunique() > 1:
            warnings.append(f"pair {pair_id} mixes categories")
        if group["expected_answer"].nunique() < len(group):
            warnings.append(f"pair {pair_id} has identical expected answers")

    return errors, warnings, df


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    errors, warnings, df = validate(path)

    print(f"Dataset: {path}")
    if df is not None and not df.empty and "category" in df.columns:
        print(f"Rows: {len(df)}")
        if "pair_id" in df.columns:
            print(f"Pairs: {df['pair_id'].replace('', pd.NA).nunique()}")
        if "language" in df.columns:
            print("By language: " + ", ".join(
                f"{k}={v}" for k, v in df["language"].value_counts().sort_index().items()))
        print("By category:")
        for cat, n in df["category"].value_counts().sort_index().items():
            print(f"  {cat:<25} {n}")

    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")

    if errors:
        print(f"FAILED ({len(errors)} error(s), {len(warnings)} warning(s))")
        return 1
    print(f"PASSED ({len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
