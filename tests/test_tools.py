import json
import pytest
from pathlib import Path
from tools import get_dataset_structure, get_dataset_statistics

CSV_CONTENT = """id,value,category
1,10.5,A
2,20.0,B
3,,A
4,15.0,A
"""

def test_get_dataset_structure_csv(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text(CSV_CONTENT)
    res = get_dataset_structure(str(p))
    assert isinstance(res, dict)
    assert res.get("dataset_name") == "data.csv"
    assert res.get("rows") == 4
    assert res.get("columns_count") == 3
    cols = [c["name"] for c in res.get("columns", [])]
    assert set(cols) == {"id", "value", "category"}
    assert res.get("shape") == [4, 3]

def test_get_dataset_statistics_csv(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text(CSV_CONTENT)
    res = get_dataset_statistics(str(p))
    assert isinstance(res, dict)
    assert res.get("shape") == [4, 3]
    stats = res.get("statistics", {})
    num = stats.get("numerical", {})
    cat = stats.get("categorical", {})

    # numerical checks
    assert num["id"]["count"] == 4
    assert num["id"]["missing"] == 0
    assert num["id"]["mean"] == pytest.approx(2.5)

    assert num["value"]["count"] == 3
    assert num["value"]["missing"] == 1
    assert num["value"]["mean"] == pytest.approx((10.5 + 20.0 + 15.0) / 3)

    # categorical checks
    category_stats = cat["category"]
    assert category_stats["unique_count"] == 2
    assert category_stats["missing"] == 0
    assert category_stats["top_values"] == {"A": 3, "B": 1}

def test_invalid_path_returns_error():
    res = get_dataset_structure("")
    assert isinstance(res, dict)
    assert "error" in res