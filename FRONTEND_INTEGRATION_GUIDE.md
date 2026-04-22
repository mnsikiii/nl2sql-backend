# Frontend Output Format & API Integration Guide

**Project**: NL2SQL Backend  
**Date**: 2026-04-22  
**Version**: 1.1.0 (Priority 1 Optimizations)  
**API Version**: v1

---

## Quick Start

### Running the Backend

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env to add:
# - DATABASE_URL=postgresql://...
# - OPENAI_API_KEY=sk-...

# 3. Run application
python app.py

# 4. Backend starts on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

### Testing the API

```bash
# Test with curl
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"question": "What is AAPL average price in the last 30 days?"}'

# Or use Python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"question": "What is AAPL average price in the last 30 days?"}
)
print(response.json())
```

---

## API Specification

### Endpoint

```
POST /query
```

### Request

```json
{
  "question": "Your natural language question here"
}
```

**Examples**:
- "What is AAPL's average closing price in the last 30 days?"
- "Compare NVDA and AAPL stock prices"
- "Show AAPL's daily prices for the last week"
- "What is the highest NVDA price this month?"

### Response Format

All responses are JSON with this structure:

```json
{
  "status": "ok|clarify|error|no_data",
  "sql": "SELECT ... FROM ...",
  "data": {
    "columns": ["col1", "col2", "col3"],
    "rows": [[val1, val2, val3], [val4, val5, val6], ...]
  },
  "final_answer": "Natural language response with insights",
  "message": "Error or info message (only when status != 'ok')",
  "safety_checks": {
    "has_injection": false,
    "has_sensitive_ops": false,
    "risk_level": "low|medium|high"
  },
  "meta": {
    "has_limit": true,
    "uses_now": false
  }
}
```

---

## Response Status Codes

### 1. Status: "ok" ✅

Successful query execution with results.

**Example Response**:
```json
{
  "status": "ok",
  "sql": "SELECT AVG(close) FROM market_data WHERE ticker='AAPL' AND timestamp >= (SELECT MAX(timestamp)-'30 days'::interval FROM market_data WHERE ticker='AAPL');",
  "data": {
    "columns": ["avg_close"],
    "rows": [[176.45]]
  },
  "final_answer": "AAPL's average closing price over the last 30 days is $176.45. The stock has shown a slight upward trend with volatility in the low range.",
  "message": "",
  "safety_checks": {
    "has_injection": false,
    "has_sensitive_ops": false,
    "risk_level": "low"
  },
  "meta": {
    "has_limit": false,
    "uses_now": false
  }
}
```

**Frontend Actions**:
- Display `final_answer` to user
- Optionally show `data` in a table
- Show success indicator ✅

---

### 2. Status: "clarify" 🤔

Question is ambiguous and needs more information from user.

**Example Response**:
```json
{
  "status": "clarify",
  "missing_slots": {
    "time_period": "Please specify the time period (e.g., 'last 30 days', 'last week', 'this month')",
    "metric": "Please clarify which metric you want (e.g., 'price', 'volume', 'volatility')"
  },
  "message": "The question needs clarification to generate an accurate query."
}
```

**Frontend Actions**:
- Display clarification request to user
- Show `missing_slots` as prompts/suggestions
- Ask user to refine their question
- Re-send query when clarified

---

### 3. Status: "no_data" 📭

Query is valid but returned no results.

**Example Response**:
```json
{
  "status": "no_data",
  "sql": "SELECT * FROM market_data WHERE ticker='INVALID' AND timestamp > '2026-01-01'",
  "data": {
    "columns": [],
    "rows": []
  },
  "message": "No data found for the given query conditions.",
  "final_answer": "Sorry, I couldn't find any data matching your query criteria."
}
```

**Frontend Actions**:
- Display "No data found" message
- Suggest alternative queries
- Allow user to refine search

---

### 4. Status: "error" ❌

Technical error during execution.

**Example Response**:
```json
{
  "status": "error",
  "sql": null,
  "data": null,
  "message": "Database connection failed: Could not connect to PostgreSQL server",
  "final_answer": "Error: Database connection failed. Please try again later."
}
```

**Frontend Actions**:
- Display error message to user
- Log error for debugging
- Suggest retry or contact support
- Don't retry automatically (indicate server issue)

---

## Real-World Output Examples

### Example 1: Simple Single-Ticker Query

**User Question**: "What is AAPL's average price in the last 30 days?"

**Backend Response**:
```json
{
  "status": "ok",
  "sql": "SELECT AVG(close) FROM market_data WHERE ticker='AAPL' AND timestamp >= (SELECT MAX(timestamp)-'30 days'::interval FROM market_data WHERE ticker='AAPL');",
  "data": {
    "columns": ["avg_close"],
    "rows": [[176.45]]
  },
  "final_answer": "AAPL's average closing price over the last 30 days is $176.45. The stock has shown a slight upward trend with volatility in the low range.",
  "message": "",
  "safety_checks": {
    "has_injection": false,
    "has_sensitive_ops": false,
    "risk_level": "low"
  },
  "meta": {
    "has_limit": false,
    "uses_now": false
  }
}
```

**Frontend Display**:
```
✅ AAPL's average closing price over the last 30 days is $176.45. 
   The stock has shown a slight upward trend with volatility in the low range.

Data Table:
┌─────────────┐
│ avg_close   │
├─────────────┤
│ $176.45     │
└─────────────┘
```

---

### Example 2: Multi-Ticker Comparison

**User Question**: "Compare NVDA and AAPL stock performance in the last 30 days"

**Backend Response**:
```json
{
  "status": "ok",
  "sql": "SELECT ticker, AVG(close) as avg_price, MAX(close) as max_price, MIN(close) as min_price, SUM(volume) as total_volume FROM market_data WHERE ticker IN ('NVDA', 'AAPL') AND timestamp >= (SELECT MAX(timestamp)-'30 days'::interval FROM market_data) GROUP BY ticker ORDER BY avg_price DESC;",
  "data": {
    "columns": ["ticker", "avg_price", "max_price", "min_price", "total_volume"],
    "rows": [
      ["NVDA", 145.67, 152.30, 138.20, 2840000000],
      ["AAPL", 172.45, 179.80, 165.30, 3120000000]
    ]
  },
  "final_answer": "Over the last 30 days:\n\n**NVDA Performance:**\n- Average Price: $145.67\n- Price Range: $138.20 - $152.30\n- Total Volume: 2.84B shares\n- Trend: Upward (↗️)\n\n**AAPL Performance:**\n- Average Price: $172.45\n- Price Range: $165.30 - $179.80\n- Total Volume: 3.12B shares\n- Trend: Moderate upward (↗️)\n\n**Comparison:**\nNVDA has higher volatility with more trading volume but lower absolute prices. AAPL shows more stable performance. Both demonstrate positive momentum.",
  "safety_checks": {
    "has_injection": false,
    "has_sensitive_ops": false,
    "risk_level": "low"
  },
  "meta": {
    "has_limit": false,
    "uses_now": false
  }
}
```

**Frontend Display**:
```
📊 NVDA vs AAPL - 30 Day Comparison

Over the last 30 days:

🔷 NVDA Performance:
   • Average Price: $145.67
   • Price Range: $138.20 - $152.30
   • Total Volume: 2.84B shares
   • Trend: Upward ↗️

🔶 AAPL Performance:
   • Average Price: $172.45
   • Price Range: $165.30 - $179.80
   • Total Volume: 3.12B shares
   • Trend: Moderate upward ↗️

📈 Comparison: NVDA has higher volatility with more trading volume but lower 
absolute prices. AAPL shows more stable performance. Both demonstrate positive momentum.

Data Table:
┌────────┬────────────┬────────────┬────────────┬──────────────┐
│ Ticker │ Avg Price  │ Max Price  │ Min Price  │ Total Volume │
├────────┼────────────┼────────────┼────────────┼──────────────┤
│ NVDA   │ $145.67    │ $152.30    │ $138.20    │ 2.84B        │
│ AAPL   │ $172.45    │ $179.80    │ $165.30    │ 3.12B        │
└────────┴────────────┴────────────┴────────────┴──────────────┘
```

---

### Example 3: Error - Clarification Needed

**User Question**: "What's better, Apple or Microsoft?"

**Backend Response**:
```json
{
  "status": "clarify",
  "missing_slots": {
    "ticker": "Please specify stock tickers: AAPL (Apple), MSFT (Microsoft), or others",
    "metric": "What metric do you want to compare? (price, volume, return, volatility)",
    "time_period": "What time period? (last 7 days, last 30 days, last quarter, etc.)"
  },
  "message": "The question needs clarification to generate an accurate query."
}
```

**Frontend Display**:
```
❓ I need some clarification to answer your question better:

1. Stock Tickers:
   Please specify: AAPL (Apple), MSFT (Microsoft), or others
   
2. Metric to Compare:
   Options: price, volume, return, volatility, etc.
   
3. Time Period:
   When? (last 7 days, last 30 days, last quarter, etc.)

🔄 Please refine your question, for example:
   "Compare AAPL and MSFT price performance over the last 30 days"
```

---

### Example 4: No Data Found

**User Question**: "What is the price of INVALID_TICKER?"

**Backend Response**:
```json
{
  "status": "no_data",
  "sql": "SELECT close FROM market_data WHERE ticker='INVALID_TICKER' LIMIT 10;",
  "data": {
    "columns": ["close"],
    "rows": []
  },
  "message": "No data found for the given query conditions.",
  "final_answer": "Sorry, I couldn't find any data for 'INVALID_TICKER'. Supported tickers are: AAPL, NVDA, TSLA, MSFT, AMZN, GOOGL, META, SPY, QQQ"
}
```

**Frontend Display**:
```
📭 No Data Found

I couldn't find any data for 'INVALID_TICKER'.

Supported tickers:
  • AAPL (Apple)
  • NVDA (NVIDIA)
  • TSLA (Tesla)
  • MSFT (Microsoft)
  • AMZN (Amazon)
  • GOOGL (Google)
  • META (Meta)
  • SPY (S&P 500 ETF)
  • QQQ (NASDAQ ETF)

Try asking about one of these tickers!
```

---

## Data Field Specifications

### `data.columns` - Array of column names
- Column names from SQL query result
- Typically: ["ticker", "close", "volume"], ["avg_price"], etc.

### `data.rows` - Array of data rows
- Each row is an array of values
- Values match column order
- May contain null values (indicated as null in JSON)
- Numbers can be integers or floats

### `final_answer` - Natural language response
- **Always included** when status is "ok"
- Generated by LLM from query results
- Incorporates **KEY INSIGHTS**:
  - Maximum/minimum values
  - Trends (increasing/decreasing/stable)
  - Volatility assessment (high/medium/low)
  - Data summaries and comparisons
- Formatted for readability with markdown

---

## Response Fields Reference

| Field | Type | When Present | Description |
|-------|------|--------------|-------------|
| status | string | Always | Query status: "ok", "clarify", "error", "no_data" |
| sql | string or null | Always | Generated SQL statement (null if error/clarify) |
| data | object | When status="ok" | Query results: {columns, rows} |
| final_answer | string | When status!="clarify" | Natural language response with insights |
| message | string | When status!="ok" | Error or info message |
| safety_checks | object | Always | Security validation results |
| meta | object | When status="ok" | Query metadata (has_limit, uses_now) |
| missing_slots | object | When status="clarify" | Clarification requirements |

---

## Priority 1 Optimizations in Output

### 1.1 Few-Shot Learning Impact
- Affects SQL generation accuracy
- Improves multi-ticker comparison queries
- Better time window calculations
- **Visible in**: `sql` field quality

### 1.2 Self-Validation & Correction
- Automatically fixes SQL errors
- Ensures GROUP BY with aggregations
- Validates time windows
- **Visible in**: Increased success rate, fewer "error" responses

### 1.3 Insights Extraction
- Auto-extracted key metrics in `final_answer`
- Includes: min/max/avg/trend/volatility
- Better context for LLM
- **Visible in**: Richer `final_answer` with insights

---

## Error Handling Best Practices

### Frontend Implementation

```javascript
// Pseudo-code for error handling

async function queryBackend(question) {
  try {
    const response = await fetch('http://localhost:8000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question })
    });
    
    const data = await response.json();
    
    switch(data.status) {
      case 'ok':
        // Display final_answer and data table
        displayAnswer(data.final_answer);
        displayDataTable(data.data);
        break;
        
      case 'clarify':
        // Ask user to refine question
        displayClarificationPrompts(data.missing_slots);
        break;
        
      case 'no_data':
        // Show helpful message
        displayMessage(data.final_answer);
        break;
        
      case 'error':
        // Show error with retry option
        displayError(data.message);
        break;
    }
    
  } catch(error) {
    // Network error
    displayError('Connection failed: ' + error.message);
  }
}
```

---

## CORS Configuration

Frontend can be on different domain. Backend allows all origins:

```python
# app.py CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (adjust in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### For Production

Update `allow_origins` to specific frontend URL:
```python
allow_origins=["https://yourdomain.com", "https://www.yourdomain.com"]
```

---

## Testing Checklist

- [ ] Successfully POST to `/query` endpoint
- [ ] Receive valid JSON response
- [ ] "ok" status returns `final_answer`
- [ ] "clarify" status provides guidance
- [ ] "no_data" status shows helpful message
- [ ] "error" status returns error details
- [ ] Data tables display correctly
- [ ] Special characters handled properly
- [ ] Large results (100+ rows) handled well
- [ ] Security checks validated

---

## Performance Considerations

- Average response time: **200-800ms**
  - 50-100ms: SQL generation
  - 20-50ms: Validation & correction
  - 100-500ms: LLM API call
  - 5-15ms: Insights extraction
  - 20-200ms: Database query

- Response timeout: **30 seconds**
- Max data rows per response: **1000** (limited by LIMIT)

---

## Supported Questions

### Single Ticker Queries
- "What is AAPL's average price in the last 30 days?"
- "Show me NVDA's closing prices for the past week"
- "What was AAPL's highest price this month?"

### Multi-Ticker Queries
- "Compare AAPL and NVDA prices"
- "Which performed better: TSLA or MSFT?"
- "Show me the average prices for AAPL, NVDA, and MSFT"

### Time-Based Queries
- "AAPL prices in the last 7 days"
- "Average volume for NVDA last month"
- "AAPL trading activity this week"

### Aggregation Queries
- "What's the total volume for AAPL?"
- "Average price across all stocks"
- "Maximum and minimum prices"

---

## Unsupported / Ambiguous Queries

❌ These will trigger "clarify" status:
- "Tell me about Apple" (needs ticker: AAPL)
- "Recent performance" (needs ticker and metric)
- "Compare better performers" (ambiguous metrics)
- No time specification with historical queries

---

## Debugging

### Check Backend Status
```bash
curl http://localhost:8000/
# Should return: {"message": "NL2SQL backend is running."}
```

### View API Documentation
```
http://localhost:8000/docs  # Swagger UI
http://localhost:8000/redoc  # ReDoc UI
```

### Monitor Logs
```bash
# Watch backend logs
tail -f app.log | grep -E "Query|SQL|error|validation"
```

---

**Version**: 1.1.0  
**Last Updated**: 2026-04-22  
**Status**: Production Ready ✅
