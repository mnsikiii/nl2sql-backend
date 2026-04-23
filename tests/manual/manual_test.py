#!/usr/bin/env python3
"""
Manual test script to inspect backend output without starting the server
"""
import json
from nl2sql import eval_one
from sql2summary import summarize_answer
from safety_checks import build_safety_checks

def test_question(question: str):
    """Test a single question and print formatted output"""
    print("\n" + "=" * 70)
    print(f"Question: {question}")
    print("=" * 70)
    
    # Step 1: Generate SQL and retrieve data
    print("\n[Step 1] eval_one() - SQL generation and execution")
    print("-" * 70)
    sql_result = eval_one(question)
    print(f"Status: {sql_result['status']}")
    
    if sql_result['status'] == 'clarify':
        print(f"Missing slots: {json.dumps(sql_result.get('missing_slots', {}), indent=2)}")
    elif sql_result['status'] == 'error':
        print(f"Error: {sql_result.get('message', 'Unknown error')}")
    elif sql_result['status'] == 'no_data':
        print(f"Message: {sql_result.get('message', 'No data found')}")
    else:
        print(f"SQL: {sql_result.get('sql', 'N/A')[:100]}...")
        if sql_result.get('data'):
            print(f"Data rows: {len(sql_result['data'].get('rows', []))}")
    
    # Step 2: Summarize answer
    print("\n[Step 2] summarize_answer() - Generate final answer")
    print("-" * 70)
    result = summarize_answer(question, sql_result)
    print(f"Final answer: {result.get('final_answer', 'N/A')[:200]}...")
    
    # Step 3: Build safety checks
    print("\n[Step 3] build_safety_checks() - Security validation")
    print("-" * 70)
    result["safety_checks"] = build_safety_checks(
        question=question,
        sql=result.get("sql"),
        status=result.get("status"),
        message=result.get("message", "")
    )
    
    print(json.dumps(result["safety_checks"], indent=2))
    
    # Final output
    print("\n[Final Response] What frontend receives:")
    print("-" * 70)
    response = {
        "status": result.get("status"),
        "final_answer": result.get("final_answer"),
        "sql": result.get("sql"),
        "data": result.get("data"),
        "missing_slots": result.get("missing_slots"),
        "safety_checks": result.get("safety_checks"),
        "meta": result.get("meta")
    }
    
    # Remove None values for cleaner output
    response = {k: v for k, v in response.items() if v is not None}
    print(json.dumps(response, indent=2, default=str))
    
    return response


def main():
    # Test cases covering all status types
    test_cases = [
        # Clarify cases
        "What is the recent performance of NVDA?",
        "Which stock performed better?",
        "What is the volatility of AAPL?",
        
        # Normal cases
        "What is the average closing price of NVDA?",
        "Show me the data for TSLA",
    ]
    
    print("\n🚀 Backend Manual Testing")
    print("Testing all status types and response formats\n")
    
    for i, question in enumerate(test_cases, 1):
        try:
            test_question(question)
        except Exception as e:
            print(f"\n❌ Error testing: {question}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✅ Manual testing complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
