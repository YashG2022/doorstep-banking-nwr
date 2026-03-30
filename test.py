import pandas as pd

file_path = r"C:\Users\cynix\Downloads\NWR_HCM (2).xls"

df = pd.read_csv(
    file_path,
    encoding="utf-16",
    sep=";",
    skiprows=1   # 🔥 SKIP "sep=;" line
)

df.columns = df.columns.str.strip()

print(df.columns)
print(df.head())