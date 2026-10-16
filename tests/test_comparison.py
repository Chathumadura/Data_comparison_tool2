import pandas as pd
import pytest

from src.comparison import ComparisonError, compare_datasets, match_columns


def test_column_matching_ignores_case_and_spacing():
    matches = match_columns(["Record ID", "Full Name"], ["record_id", "FULL-NAME"])
    pairs = {(m["a"], m["b"]) for m in matches}
    assert ("Record ID", "record_id") in pairs
    assert ("Full Name", "FULL-NAME") in pairs


def test_compare_identifies_matches_mismatches_and_missing_rows():
    a = pd.DataFrame({"ID":[1,2,3], "Name":["Alice","Bob","Cara"], "Amount":[10.0,20.0,30.0]})
    b = pd.DataFrame({"id":[1,2,4], "name":["alice","Bobby","Dana"], "amount":[10.0,20.0,40.0]})
    result = compare_datasets(a, b, [("ID","id")], ignore_case=True)
    assert result["summary"]["common_keys"] == 2
    assert result["summary"]["matched_rows"] == 1
    assert result["summary"]["mismatched_rows"] == 1
    assert result["summary"]["only_a"] == 1
    assert result["summary"]["only_b"] == 1


def test_numeric_tolerance_is_applied():
    a = pd.DataFrame({"ID":[1], "Value":[100.0]})
    b = pd.DataFrame({"ID":[1], "Value":[100.04]})
    exact = compare_datasets(a, b, [("ID","ID")], numeric_tolerance=0.0)
    tolerant = compare_datasets(a, b, [("ID","ID")], numeric_tolerance=0.05)
    assert exact["summary"]["mismatched_rows"] == 1
    assert tolerant["summary"]["matched_rows"] == 1


def test_duplicate_keys_require_more_key_columns():
    a = pd.DataFrame({"ID":[1,1], "Value":["A","B"]})
    b = pd.DataFrame({"ID":[1], "Value":["A"]})
    with pytest.raises(ComparisonError, match="not unique"):
        compare_datasets(a, b, [("ID","ID")])
