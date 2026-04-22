"""Application constants and configurations"""

# ==================== Database Schema ====================
DB_SCHEMA = """
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

# ==================== Allowed Resources ====================
ALLOWED_TABLES = {"market_data"}
ALLOWED_COLUMNS = {"ticker", "timestamp", "open", "high", "low", "close", "volume"}

# ==================== Supported Data ====================
SUPPORTED_TICKERS = ["nvda", "aapl", "tsla", "msft", "amzn", "googl", "meta", "spy", "qqq"]

# ==================== Clarification Keywords ====================
AMBIGUOUS_KEYWORDS = [
    "recent",
    "performed better",
    "performed worse",
    "volatility",
    "trend",
    "performance",
    "better",
    "worse",
    "highest",
    "lowest",
    "top",
    "bottom",
    "most",
    "least",
]

TIME_INDICATORS = ["recent", "last", "past", "week", "month", "year", "day", "days"]

COMPARISON_INDICATORS = ["better", "worse", "than", "compared to", "vs", "versus"]

VOLATILITY_MEASURES = ["standard deviation", "variance", "range", "beta", "stdev", "vix"]

PERFORMANCE_METRICS = ["return", "price change", "volume", "market cap", "performance of"]

# ==================== SQL Rules ====================
DEFAULT_LIMIT = 200
SQL_KEYWORDS_BANNED = [
    "drop ",
    "delete ",
    "update ",
    "insert ",
    "alter ",
    "create ",
    "truncate ",
    "grant ",
    "revoke ",
]

# ==================== Data Processing ====================
FLOAT_TOLERANCE = 1e-6

# ==================== LLM Prompts ====================
SQL_GENERATION_PROMPT_TEMPLATE = """
You are a PostgreSQL expert. Generate SQL following Chain-of-Thought methodology.

STEP 1: ANALYZE THE QUESTION
- Identify the metrics requested (price, volume, volatility, etc.)
- Identify the tickers involved
- Identify the time period
- Identify any aggregations or comparisons needed

STEP 2: DETERMINE THE QUERY TYPE
- Is this a single ticker query or multi-ticker comparison?
- Should results be aggregated (SUM, AVG, MAX, MIN)?
- Do we need to group by ticker or time?

STEP 3: CONSTRUCT THE SQL
Apply these rules STRICTLY:
- Do NOT include markdown code fences: no ``` symbols
- Do NOT include explanations or comments
- Use double quotes around column names like "timestamp"
- Only query from table market_data
- Always add LIMIT {limit} for non-aggregation queries
- For multi-ticker comparison, use GROUP BY ticker when appropriate
- For time-based queries, anchor to latest available data:
  * Use MAX("timestamp") to find the most recent data point
  * When filtering by ticker, compute MAX("timestamp") within that ticker scope
  * For multi-ticker queries, use MAX("timestamp") over the selected tickers

TIME WINDOW RULES:
- Never use NOW() - always use MAX("timestamp") for historical data
- If user mentions "recent", "last N days", or "past N days":
  * Calculate the date range from the latest available timestamp
  * Example: If latest date is 2025-01-20, "last 5 days" = 2025-01-15 to 2025-01-20

GOOD EXAMPLES (patterns to follow):
Example 1 - Average Price:
  Question: "What is NVDA's average closing price in the last 30 days?"
  SQL: SELECT AVG(close) FROM market_data WHERE ticker='NVDA' AND "timestamp" >= (SELECT MAX("timestamp")-'30 days'::interval FROM market_data WHERE ticker='NVDA');
  Why: Uses MAX with ticker scope, aggregates correctly, no unnecessary LIMIT

Example 2 - Multi-ticker Comparison:
  Question: "Compare NVDA and AAPL closing prices"
  SQL: SELECT ticker, AVG(close) as avg_close FROM market_data WHERE ticker IN ('NVDA','AAPL') GROUP BY ticker;
  Why: Uses proper GROUP BY, correct AVG function, reasonable LIMIT for non-aggregation

Example 3 - Recent Trend:
  Question: "Show NVDA's daily prices for the last week"
  SQL: SELECT "timestamp", close FROM market_data WHERE ticker='NVDA' AND "timestamp" >= (SELECT MAX("timestamp")-'7 days'::interval FROM market_data WHERE ticker='NVDA') ORDER BY "timestamp" DESC LIMIT 7;
  Why: Proper time filtering, double quotes on timestamp, includes LIMIT for non-aggregation

BAD EXAMPLES (patterns to AVOID):
❌ Bad Example 1 - Wrong aggregation:
  Question: "What is NVDA's total revenue?"
  SQL: SELECT AVG(close) FROM market_data WHERE ticker='NVDA';
  Problem: Uses AVG for what should be SUM or detailed data. Missing time scope.

❌ Bad Example 2 - Using NOW():
  Question: "NVDA price in the last 30 days"
  SQL: SELECT close FROM market_data WHERE ticker='NVDA' AND "timestamp" > NOW() - interval '30 days';
  Problem: Uses NOW() instead of MAX("timestamp"). Doesn't work for historical data.

❌ Bad Example 3 - No GROUP BY:
  Question: "Compare NVDA vs AAPL"
  SQL: SELECT ticker, close FROM market_data WHERE ticker IN ('NVDA','AAPL');
  Problem: No GROUP BY or aggregation. Returns too many rows without structure.

Schema:
{schema}

User question:
{question}

Remember: Output ONLY the SQL statement, nothing else."""

ANSWER_SUMMARY_PROMPT_TEMPLATE = """
You are a financial data assistant. Your task is to generate clear, concise answers based on data.

ANALYSIS FRAMEWORK:
1. Extract key numbers from the data (prices, volumes, changes)
2. Identify trends or patterns
3. Compare across tickers if multi-ticker data
4. Provide actionable insights

FORMATTING RULES:
- Be concise but informative (2-3 sentences for simple queries, up to 5 for complex)
- Use precise numbers with context (e.g., "NVDA closed at $145.32, up 2.5%")
- For comparisons, clearly state the direction (higher/lower/better/worse)
- For time-series data, describe the trend
- For aggregations, highlight the most relevant statistics

OUTPUT STRUCTURE:
1. Direct answer to the question
2. Key supporting numbers from the data
3. Any important qualifications or data limitations

User Question:
{question}

SQL Query:
{sql}

Data Columns: {columns}
Data Rows:
{rows}

Generate a direct, fact-based answer:
"""
