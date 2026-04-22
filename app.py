from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


from nl2sql import eval_one
from sql2summary import summarize_answer
from safety_checks import build_safety_checks

app = FastAPI(title="NL2SQL Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # Allow all origins for now, restrict later in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": "NL2SQL backend is running."}

@app.post("/query")
def query(req: QueryRequest):
    # return eval_one(req.question)
    sql_res = eval_one(req.question)
    result = summarize_answer(req.question, sql_res)
    result["safety_checks"] = build_safety_checks(
        question=req.question,
        sql=result.get("sql"),
        status=result.get("status"),
        message=result.get("message", "")
    )

    return result