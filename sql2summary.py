from openai import OpenAI
import os
from dotenv import load_dotenv


load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# This module takes the output from nl2sql and generates a concise summary answer for the user.
def summarize_answer(question: str, result: dict) -> dict:
    status = result.get("status")

    # error case
    if status == "error":
        result["final_answer"] = f"Error: {result.get('message', '')}"
        return result

    # no data case
    if status == "no_data":
        result["final_answer"] = result.get(
            "message",
            "No data was found for this query."
        )
        return result

    columns = result["data"]["columns"]
    rows = result["data"]["rows"]

    prompt = f"""
You are a financial data assistant.

Answer the user's question ONLY using the SQL result below.
Do not invent facts.
Be concise and clear.

User Question:
{question}

SQL:
{result.get("sql", "")}

Columns:
{columns}

Rows:
{rows}

Write the final answer:
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    answer = response.choices[0].message.content.strip()
    result["final_answer"] = answer
    return result

def answer_one(question: str):
    from nl2sql import eval_one
    sql_result = eval_one(question)
    final_result = summarize_answer(question, sql_result)
    
    return final_result
