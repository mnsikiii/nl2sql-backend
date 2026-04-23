import json
import csv
from sql2summary import answer_one


def load_dataset(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data.append(json.loads(line))
    return data


def run_summary_eval(dataset_path):
    dataset = load_dataset(dataset_path)
    results = []

    for case in dataset:
        qid = case["id"]
        question = case["question"]
        expected_behavior = case.get("expected_behavior", "")
        category = case.get("category", "")

        print(f"Running {qid}: {question}")

        result = answer_one(question)

        row = {
            "id": qid,
            "category": category,
            "question": question,
            "expected_behavior": expected_behavior,
            "pred_status": result.get("status"),
            "sql": result.get("sql"),
            "data_columns": json.dumps(result.get("data", {}).get("columns", []), ensure_ascii=False),
            "data_rows": json.dumps(result.get("data", {}).get("rows", []), ensure_ascii=False),
            "final_answer": result.get("final_answer", ""),
            "message": result.get("message", ""),
            "has_limit": result.get("meta", {}).get("has_limit"),
            "uses_now": result.get("meta", {}).get("uses_now"),

            # 留给 B 填
            "result_correct": "",
            "answer_faithful_to_data": "",
            "answer_satisfies_request": "",
            "needs_clarification": "",
            "notes": ""
        }

        results.append(row)

    return results


def save_csv(results, path):
    if not results:
        return
    keys = list(results[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(results)


def save_json(results, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    dataset_path = "./dataset/summary_eval_v1.jsonl"
    results = run_summary_eval(dataset_path)

    save_csv(results, "./output/summary_eval_report_v1.csv")
    save_json(results, "./output/summary_eval_report_v1.json")

    print("Saved:")
    print("- summary_eval_report_v1.csv")
    print("- summary_eval_report_v1.json")