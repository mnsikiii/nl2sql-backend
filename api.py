from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

from nl2sql import eval_one

app = FastAPI(title="NL2SQL Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # 先全开，后面再收紧
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
    return eval_one(req.question)