import re


ALLOWED_TABLES = {"market_data"}
ALLOWED_COLUMNS = {"ticker", "timestamp", "open", "high", "low", "close", "volume"}


def check_select_only(sql: str) -> bool:
    s = sql.strip().lower()
    return s.startswith("select") or s.startswith("with")


def check_no_table_modification(sql: str) -> bool:
    s = sql.lower()
    banned = [
        "drop ", "delete ", "update ", "insert ",
        "alter ", "create ", "truncate ", "grant ", "revoke "
    ]
    return not any(b in s for b in banned)


def check_source_correct(sql: str) -> bool:
    """
    当前定义：只能访问 market_data
    """
    s = sql.lower()

    # 粗略找 from / join 后面的表名
    tables = re.findall(r"\b(?:from|join)\s+([a-zA-Z_][a-zA-Z0-9_]*)", s)
    if not tables:
        return False

    return all(t in ALLOWED_TABLES for t in tables)


def check_time_window_correct(question: str, sql: str) -> bool:
    """
    当前定义：
    1. 如果问题涉及 recent / last / past / week / month / year / today / yesterday，
       则 SQL 不应使用 NOW()
    2. 如果问题提到了 ticker，则时间窗口应尽量在 ticker scope 内取 MAX(timestamp)
    注意：这是规则性检查，不是严格语义证明
    """
    q = question.lower()
    s = sql.lower()

    time_keywords = [
        "recent", "last", "past", "week", "month", "year",
        "today", "yesterday", "day", "days", "trading week"
    ]
    needs_time_rule = any(k in q for k in time_keywords)

    if not needs_time_rule:
        return True

    if "now(" in s:
        return False

    # 如果问题里有明确 ticker，尽量要求 MAX(timestamp) 同 scope 出现
    tickers = ["nvda", "aapl", "tsla", "msft", "amzn", "googl", "meta"]
    mentioned = [t.upper() for t in tickers if t in q]

    if mentioned:
        # 至少应出现 max("timestamp") 或 max(timestamp)
        if 'max("timestamp")' not in s and "max(timestamp)" not in s:
            return False

    return True


def check_permission_granted(exec_status: str, error_message: str = "") -> bool:
    """
    当前定义：后端是否具备执行权限。
    如果执行成功/有结果/no_data，都算有权限。
    如果数据库权限类报错，则返回 False。
    """
    if exec_status in {"ok", "no_data"}:
        return True

    msg = (error_message or "").lower()
    permission_markers = ["permission denied", "not authorized", "insufficient privilege"]
    if any(m in msg for m in permission_markers):
        return False

    # 其他 error 先默认 True（因为可能是 SQL 逻辑错，不是权限问题）
    return True


def build_safety_checks(question: str, sql: str, status: str, message: str = "") -> dict:
    return {
        "select_only": check_select_only(sql) if sql else False,
        "source_correct": check_source_correct(sql) if sql else False,
        "time_window_correct": check_time_window_correct(question, sql) if sql else False,
        "permission_granted": check_permission_granted(status, message),
        "no_table_modification": check_no_table_modification(sql) if sql else False,
    }