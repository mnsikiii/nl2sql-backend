"""API route endpoints"""
from fastapi import APIRouter, HTTPException, status

from src.core.nl2sql import eval_one
from src.core.sql2summary import summarize_answer
from src.core.safety_checks import build_safety_checks
from src.models import QueryRequest, QueryResponse
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Create router for API v1
router = APIRouter(prefix="/api/v1", tags=["query"])


@router.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    logger.info("Health check requested")
    return {"status": "healthy", "service": "NL2SQL Backend"}


@router.post("/query", response_model=QueryResponse, status_code=200)
async def query(req: QueryRequest) -> QueryResponse:
    """
    Process a natural language question.
    
    This endpoint implements the complete NL2SQL pipeline:
    1. Check if clarification is needed
    2. Generate SQL from question
    3. Execute SQL query
    4. Summarize results
    5. Perform safety checks
    
    Args:
        req: Query request with natural language question
        
    Returns:
        QueryResponse with status, answer, SQL, data, and safety checks
        
    Raises:
        HTTPException: If internal error occurs
        
    Example:
        POST /api/v1/query
        {"question": "What is the average closing price of NVDA?"}
        
        Response:
        {
            "status": "ok",
            "final_answer": "The average closing price is $100.23",
            "sql": "SELECT AVG(close) FROM market_data WHERE ticker='NVDA'",
            "data": {...},
            "safety_checks": {...}
        }
    """
    try:
        logger.info(f"Processing query: {req.question}")
        
        # Step 1: SQL generation and execution
        sql_result = eval_one(req.question)
        
        # Step 2: Summarize answer
        result = summarize_answer(req.question, sql_result)
        
        # Step 3: Build safety checks
        result["safety_checks"] = build_safety_checks(
            question=req.question,
            sql=result.get("sql"),
            status=result.get("status"),
            message=result.get("message", ""),
        )
        
        logger.info(f"Query processed successfully. Status: {result['status']}")
        
        # Build response
        response = QueryResponse(
            status=result["status"],
            message=result.get("message", ""),
            final_answer=result.get("final_answer"),
            sql=result.get("sql"),
            data=result.get("data"),
            missing_slots=result.get("missing_slots"),
            safety_checks=result.get("safety_checks"),
            meta=result.get("meta"),
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
