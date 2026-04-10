
# 最小 Python 查询测试脚本


from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://neondb_owner:npg_E1ORCYPudZf8@ep-jolly-lake-aiqvtx3p-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(DATABASE_URL)

# sample test query
with engine.connect() as conn:
    result = conn.execute(text("""
        SELECT ticker, COUNT(*)
        FROM market_data
        GROUP BY ticker;
    """))
    
    for row in result:
        print(row)
