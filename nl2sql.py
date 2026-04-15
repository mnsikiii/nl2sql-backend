import os
from sqlalchemy import create_engine, text
from openai import OpenAI
import re
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# export DATABASE_URL=""
# export OPENAI_API_KEY=""


client = OpenAI(api_key=OPENAI_API_KEY)
engine = create_engine(DATABASE_URL)

SCHEMA = """
Table: market_data
Columns:
- ticker (TEXT)
- timestamp (TIMESTAMPTZ)
- open (DOUBLE)
- high (DOUBLE)
- low (DOUBLE)
- close (DOUBLE)
- volume (BIGINT)
"""

# This module takes a natural language question, generates SQL, runs it against the database, and returns the results in a structured format.
def generate_sql(question):
    prompt = f"""
You are a PostgreSQL expert.
Generate ONLY raw SQL.

Rules:
- Do NOT include markdown
- Do NOT include explanations
- Use double quotes around "timestamp"
- Only query from table market_data
- Always add LIMIT 200 for non-aggregation queries
- For multi-ticker comparison, use GROUP BY ticker when appropriate

Time Rules:
- Never use NOW() for historical market data
- If the user asks for "recent", "last N days", or "past N days",
  anchor the time window to the latest available timestamp in the dataset
  using MAX("timestamp")
- NEVER use MAX(timestamp) from the whole table when a ticker is specified
- ALWAYS compute MAX("timestamp") within the same ticker scope
- For multi-ticker queries, use MAX("timestamp") over the selected tickers

Schema:
{SCHEMA}

User question:
{question}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    sql = response.choices[0].message.content.strip()

    # Remove markdown code fences if present
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql


# Run the generated SQL and return results in a structured format
def run_sql(sql: str):
    with engine.connect() as conn:
        result = conn.execute(text(sql))
        cols = list(result.keys())
        rows = []
        for r in result.fetchall():
            # 处理 datetime 等不可 JSON 序列化对象
            rr = []
            for v in r:
                if hasattr(v, "isoformat"):
                    rr.append(v.isoformat())
                else:
                    rr.append(v)
            rows.append(rr)
        return {"columns": cols, "rows": rows}

# -------------------- #
# Security layer
# -------------------- #

def clean_sql(raw: str) -> str:
    sql = raw.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def enforce_select_only(sql: str) -> str:
    s = sql.strip().lower()

    # forbid multiple statements: only one statement allowed (simple rule: at most one semicolon, and it can only be at the end)
    if ";" in sql.strip()[:-1]:
        raise ValueError("Rejected: multiple SQL statements detected.")

    # must be SELECT or WITH ... SELECT
    if not (s.startswith("select") or s.startswith("with")):
        raise ValueError("Rejected: only SELECT queries are allowed.")

    # forbid dangerous keywords (minimal blacklist)
    banned = ["drop ", "delete ", "update ", "insert ", "alter ", "create ", "truncate ", "grant ", "revoke "]
    if any(b in s for b in banned):
        raise ValueError("Rejected: dangerous SQL keyword detected.")

    return sql

def ensure_limit(sql: str, default_limit: int = 200) -> str:
    # add limit if not present
    if re.search(r"\blimit\b", sql, flags=re.IGNORECASE):
        return sql.rstrip(";") + ";"
    if "avg(" in sql.lower() or "sum(" in sql.lower() or "max(" in sql.lower():
        return sql
    return sql.rstrip(";") + f"\nLIMIT {default_limit};"

# zip all security steps together
def secure_sql(raw_sql: str) -> str:
    sql = clean_sql(raw_sql)
    sql = enforce_select_only(sql)
    sql = ensure_limit(sql)
    return sql



# -------------------- #
# change output format to a standard protocol
# -------------------- #

def eval_one(question: str):
    try:
        raw_sql = generate_sql(question)
        sql = secure_sql(raw_sql)
        data = run_sql(sql)

        if len(data["rows"]) == 0:
            return {
                "status": "no_data",
                "sql": sql,
                "data": data,
                "message": "No data found for the given query conditions."
            }

        if all(all(v is None for v in row) for row in data["rows"]):
            return {
                "status": "no_data",
                "sql": sql,
                "data": data,
                "message": "Query executed but returned no valid values."
            }

        return {
            "status": "ok",
            "sql": sql,
            "data": data,
            "message": "",
            "meta": {
                "has_limit": "limit" in sql.lower(),
                "uses_now": "now(" in sql.lower()
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "sql": None,
            "data": None,
            "message": str(e)
        }




if __name__ == "__main__":
    question = input("Ask: ")
    out = eval_one(question)
    print("\nOutput:\n", out)
