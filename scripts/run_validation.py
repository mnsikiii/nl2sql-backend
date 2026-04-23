import json
from nl2sql import eval_one, run_sql

def load_dataset(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                data.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"JSON error on line {i}: {line}")
                raise
    return data

def compare_results(pred, gold):
    # easy version: exact match of rows and columns
    # return pred["columns"] == gold["columns"] and pred["rows"] == gold["rows"]
    # ignore alias
    return pred["rows"] == gold["rows"]


def run_validation(dataset_path):
    dataset = load_dataset(dataset_path)

    results = []

    for case in dataset:
        question = case["question"]
        gold_sql = case["gold_sql"]

        print(f"\nRunning: {question}")

        pred = eval_one(question)

        try:
            gold_result = run_sql(gold_sql)
        except Exception as e:
            gold_result = None

        match = False
        if pred["status"] == "ok" and gold_result is not None:
            match = compare_results(pred["data"], gold_result)

        result = {
            "id": case["id"],
            "question": question,
            "pred_sql": pred["sql"],
            "gold_sql": gold_sql,
            "status": pred["status"],
            "match": match
        }

        results.append(result)

    return results


if __name__ == "__main__":
    results = run_validation("golden_sql.jsonl")

    with open("validation_report.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\nValidation complete!")