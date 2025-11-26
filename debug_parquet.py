import pandas as pd
from pathlib import Path

# 打开文件
file_path = Path("data_test/raw/ib/chain/view=intraday/date=2025-11-14/underlying=AAPL/exchange=SMART/part-000.parquet")
df = pd.read_parquet(file_path)

# 在 VSCode 中查看 df
print(df)
