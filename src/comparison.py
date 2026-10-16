from __future__ import annotations

import re
from typing import Iterable

import pandas as pd
from pandas.api.types import is_numeric_dtype


class ComparisonError(ValueError):
    pass


def normalize_column_name(name: object) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).strip().lower())


def match_columns(columns_a: Iterable[object], columns_b: Iterable[object]) -> list[dict[str, object]]:
    buckets_a, buckets_b = {}, {}
    for col in columns_a:
        buckets_a.setdefault(normalize_column_name(col), []).append(str(col))
    for col in columns_b:
        buckets_b.setdefault(normalize_column_name(col), []).append(str(col))

    matches = []
    for normalized in sorted(set(buckets_a) & set(buckets_b)):
        if len(buckets_a[normalized]) == 1 and len(buckets_b[normalized]) == 1:
            a_col, b_col = buckets_a[normalized][0], buckets_b[normalized][0]
            matches.append({"a": a_col, "b": b_col, "exact": a_col == b_col})
    return matches


def _key_value(value, trim_whitespace: bool, ignore_case: bool):
    if pd.isna(value):
        return "<NULL>"
    if isinstance(value, str):
        value = value.strip() if trim_whitespace else value
        return value.casefold() if ignore_case else value
    return value


def _series_equal(a, b, trim_whitespace: bool, ignore_case: bool, tolerance: float):
    both_null = a.isna() & b.isna()
    one_null = a.isna() ^ b.isna()

    if is_numeric_dtype(a.dtype) and is_numeric_dtype(b.dtype):
        aa = pd.to_numeric(a, errors="coerce")
        bb = pd.to_numeric(b, errors="coerce")
        equal = (aa - bb).abs().le(tolerance).fillna(False)
    else:
        aa, bb = a.astype("string"), b.astype("string")
        if trim_whitespace:
            aa, bb = aa.str.strip(), bb.str.strip()
        if ignore_case:
            aa, bb = aa.str.casefold(), bb.str.casefold()
        equal = aa.eq(bb).fillna(False)

    return (equal | both_null) & ~one_null


def _indexed(df, keys, trim_whitespace, ignore_case):
    prepared = df.copy()
    internal = []
    for idx, key in enumerate(keys):
        name = f"__key_{idx}"
        internal.append(name)
        prepared[name] = prepared[key].map(lambda v: _key_value(v, trim_whitespace, ignore_case))

    dup = prepared.duplicated(subset=internal, keep=False)
    if dup.any():
        raise ComparisonError(
            f"Selected key column(s) are not unique ({int(dup.sum())} duplicate rows). "
            "Add another key column so each record is uniquely identified."
        )
    return prepared.set_index(internal, drop=False), internal


def compare_datasets(
    df_a: pd.DataFrame,
    df_b: pd.DataFrame,
    key_pairs: list[tuple[str, str]],
    *,
    trim_whitespace: bool = True,
    ignore_case: bool = True,
    numeric_tolerance: float = 0.0,
):
    if not key_pairs:
        raise ComparisonError("Select at least one key column.")
    if numeric_tolerance < 0:
        raise ComparisonError("Numeric tolerance cannot be negative.")

    keys_a = [a for a, _ in key_pairs]
    keys_b = [b for _, b in key_pairs]

    indexed_a, internal_keys = _indexed(df_a, keys_a, trim_whitespace, ignore_case)
    indexed_b, _ = _indexed(df_b, keys_b, trim_whitespace, ignore_case)

    only_a_idx = indexed_a.index.difference(indexed_b.index)
    only_b_idx = indexed_b.index.difference(indexed_a.index)
    common_idx = indexed_a.index.intersection(indexed_b.index)

    only_a = indexed_a.loc[only_a_idx, df_a.columns].reset_index(drop=True)
    only_b = indexed_b.loc[only_b_idx, df_b.columns].reset_index(drop=True)
    common_a = indexed_a.loc[common_idx, df_a.columns]
    common_b = indexed_b.loc[common_idx, df_b.columns]

    all_matches = match_columns(df_a.columns, df_b.columns)
    key_pairs_set = set(key_pairs)
    compare_pairs = [m for m in all_matches if (m["a"], m["b"]) not in key_pairs_set]
    if not compare_pairs:
        raise ComparisonError("No comparable non-key columns were found.")

    row_mismatch = pd.Series(False, index=common_idx, dtype=bool)
    mismatch_labels = {key: [] for key in common_idx}
    detail_frames = []

    for match in compare_pairs:
        col_a, col_b = match["a"], match["b"]
        equal = _series_equal(common_a[col_a], common_b[col_b], trim_whitespace, ignore_case, numeric_tolerance)
        bad = ~equal
        if not bad.any():
            continue

        row_mismatch = row_mismatch | bad
        label = col_a if col_a == col_b else f"{col_a} ↔ {col_b}"
        for key in bad[bad].index:
            mismatch_labels[key].append(label)

        av = common_a.loc[bad, col_a]
        bv = common_b.loc[bad, col_b]
        detail = pd.DataFrame({
            "Column A": col_a,
            "Column B": col_b,
            "Value A": av.astype(object).values,
            "Value B": bv.astype(object).values,
        }, index=av.index).reset_index()

        rename_map = {
            internal: (keys_a[i] if keys_a[i] == keys_b[i] else f"{keys_a[i]} ↔ {keys_b[i]}")
            for i, internal in enumerate(internal_keys)
        }
        detail.rename(columns=rename_map, inplace=True)
        detail_frames.append(detail)

    matched_idx = row_mismatch[~row_mismatch].index
    mismatched_idx = row_mismatch[row_mismatch].index

    matched_rows = common_a.loc[matched_idx, df_a.columns].reset_index(drop=True)
    mismatched_rows = common_a.loc[mismatched_idx, df_a.columns].copy()
    if len(mismatched_rows):
        mismatched_rows["Mismatched Columns"] = [", ".join(mismatch_labels[k]) for k in mismatched_idx]
    mismatched_rows = mismatched_rows.reset_index(drop=True)

    mismatch_details = pd.concat(detail_frames, ignore_index=True) if detail_frames else pd.DataFrame(
        columns=["Column A", "Column B", "Value A", "Value B"]
    )
    breakdown = (
        mismatch_details["Column A"].value_counts().rename_axis("Column").reset_index(name="Mismatch Count")
        if not mismatch_details.empty else pd.DataFrame(columns=["Column", "Mismatch Count"])
    )

    mapping = pd.DataFrame([
        {
            "Dataset A": m["a"],
            "Dataset B": m["b"],
            "Exact Name Match": m["exact"],
            "Used as Key": (m["a"], m["b"]) in key_pairs_set,
        }
        for m in all_matches
    ])

    summary = {
        "rows_a": len(df_a),
        "rows_b": len(df_b),
        "common_keys": len(common_idx),
        "matched_rows": len(matched_rows),
        "mismatched_rows": len(mismatched_rows),
        "only_a": len(only_a),
        "only_b": len(only_b),
        "compared_columns": len(compare_pairs),
        "cell_mismatches": len(mismatch_details),
    }

    return {
        "summary": summary,
        "matched_rows": matched_rows,
        "mismatched_rows": mismatched_rows,
        "mismatch_details": mismatch_details,
        "only_a": only_a,
        "only_b": only_b,
        "mismatch_breakdown": breakdown,
        "column_mapping": mapping,
    }
