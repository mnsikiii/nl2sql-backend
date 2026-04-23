import csv
import json
import math
from pathlib import Path
from typing import Any, Dict, List

from nl2sql import eval_one, run_sql

DATASET_PATH = Path("./dataset/validation_v1.jsonl")
REPORT_JSON_PATH = Path("./output/validation_report_v1.json")
REPORT_CSV_PATH = Path("./output/validation_report_v1.csv")

FLOAT_TOL = 1e-6


def load_dataset(path: Path) -> List[Dict[str, Any]]:
    data: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON on line {i}: {e}") from e
    return data


def normalize_value(v: Any) -> Any:
    if isinstance(v, float):
        return round(v, 10)
    return v


def values_equal(a: Any, b: Any, tol: float = FLOAT_TOL) -> bool:
    if a is None and b is None:
        return True
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)
    return a == b


def rows_equal(pred_rows: List[List[Any]], gold_rows: List[List[Any]]) -> bool:
    if len(pred_rows) != len(gold_rows):
        return False
    for pred_row, gold_row in zip(pred_rows, gold_rows):
        if len(pred_row) != len(gold_row):
            return False
        for a, b in zip(pred_row, gold_row):
            if not values_equal(a, b):
                return False
    return True


def sort_rows_if_needed(rows: List[List[Any]]) -> List[List[Any]]:
    def key_fn(row: List[Any]):
        return tuple("" if x is None else str(normalize_value(x)) for x in row)
    return sorted(rows, key=key_fn)


def compare_results(pred: Dict[str, Any], gold: Dict[str, Any]) -> bool:
    pred_rows = pred.get("rows", [])
    gold_rows = gold.get("rows", [])

    # Compare row content only, ignoring column aliases.
    # Sort rows to avoid false negatives from row ordering differences.
    pred_rows = sort_rows_if_needed(pred_rows)
    gold_rows = sort_rows_if_needed(gold_rows)
    return rows_equal(pred_rows, gold_rows)



def classify_error(pred: Dict[str, Any], match: bool) -> str | None:
    if pred["status"] != "ok":
        return pred["status"]
    if match:
        return None

    sql = (pred.get("sql") or "").lower()
    if "now(" in sql:
        return "time_anchor_error"
    if any(fn in sql for fn in ["avg(", "sum(", "max(", "min("]):
        return "aggregation_or_comparison_error"
    return "result_mismatch"


def run_validation(dataset_path: Path) -> List[Dict[str, Any]]:
    dataset = load_dataset(dataset_path)
    results: List[Dict[str, Any]] = []

    for case in dataset:
        question = case["question"]
        gold_sql = case["gold_sql"]

        print(f"Running {case['id']}: {question}")

        pred = eval_one(question)
        gold_result = run_sql(gold_sql)

        match = False
        if pred["status"] == case.get("expected_status", "ok") == "ok":
            match = compare_results(pred["data"], gold_result)

        result = {
            "id": case["id"],
            "category": case["category"],
            "question": question,
            "expected_status": case.get("expected_status", "ok"),
            "pred_status": pred["status"],
            "pred_sql": pred.get("sql"),
            "gold_sql": gold_sql,
            "match": match,
            "error_type": classify_error(pred, match),
            "meta": pred.get("meta", {}),
        }
        results.append(result)

    return results


def summarize(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    total = len(results)
    ok_count = sum(1 for r in results if r["pred_status"] == "ok")
    match_count = sum(1 for r in results if r["match"])
    now_violations = sum(1 for r in results if r.get("meta", {}).get("uses_now"))

    by_category: Dict[str, Dict[str, int]] = {}
    for r in results:
        cat = r["category"]
        by_category.setdefault(cat, {"total": 0, "matched": 0})
        by_category[cat]["total"] += 1
        by_category[cat]["matched"] += int(r["match"])

    return {
        "total": total,
        "ok_count": ok_count,
        "match_count": match_count,
        "accuracy": match_count / total if total else 0.0,
        "execution_success_rate": ok_count / total if total else 0.0,
        "now_violations": now_violations,
        "by_category": by_category,
    }


def save_reports(results: List[Dict[str, Any]]):
    summary = summarize(results)
    payload = {
        "summary": summary,
        "results": results,
    }

    with REPORT_JSON_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    with REPORT_CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "id",
                "category",
                "question",
                "expected_status",
                "pred_status",
                "match",
                "error_type",
                "pred_sql",
                "gold_sql",
            ],
        )
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "id": r["id"],
                    "category": r["category"],
                    "question": r["question"],
                    "expected_status": r["expected_status"],
                    "pred_status": r["pred_status"],
                    "match": r["match"],
                    "error_type": r["error_type"],
                    "pred_sql": r["pred_sql"],
                    "gold_sql": r["gold_sql"],
                }
            )

    print("\nSummary:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    print(f"\nSaved JSON report to {REPORT_JSON_PATH}")
    print(f"Saved CSV report to {REPORT_CSV_PATH}")


if __name__ == "__main__":
    results = run_validation(DATASET_PATH)
    save_reports(results)
