import os
import glob
import pandas as pd
from sqlalchemy import create_engine

# DATABASE_URL = os.environ["postgresql://neondb_owner:npg_E1ORCYPudZf8@ep-jolly-lake-aiqvtx3p-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"]  # my Neon connection string
DATABASE_URL = "postgresql://neondb_owner:npg_E1ORCYPudZf8@ep-jolly-lake-aiqvtx3p-pooler.c-4.us-east-1.aws.neon.tech/neondb?sslmode=require"
DATA_DIR = os.path.expanduser("~/Downloads/data")  # 改成你的文件夹

engine = create_engine(DATABASE_URL)

files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
assert files, f"No csv files found in {DATA_DIR}"

all_df = []
for fp in files:
    ticker = os.path.splitext(os.path.basename(fp))[0].upper()  # AMZN.csv -> AMZN

    df = pd.read_csv(fp, header=None, names=["timestamp","open","high","low","close","volume"])

    df = df.rename(columns={df.columns[0]: "ts_excel"})  # 第一列是 timestamp 数值
    df["ticker"] = ticker
    df = df[["ticker", "ts_excel", "open", "high", "low", "close", "volume"]]
    all_df.append(df)

big = pd.concat(all_df, ignore_index=True)

# 写入 staging_market_data（覆盖/追加按需）
big.to_sql("staging_market_data", engine, if_exists="append", index=False, method="multi", chunksize=5000)

print("Loaded rows:", len(big))
