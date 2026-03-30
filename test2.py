import pandas as pd

file_path = r"C:\Users\cynix\Desktop\doorstep-banking\RAIL_SHAKTI_EXTRACT_17032026.txt"

data = []

with open(file_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

for line in lines:
    if "Total Amount" in line or "BRANCH" in line:
        continue

    parts = line.split()

    if len(parts) < 5:
        continue

    row = {}

    # Assign A, B, C, D...
    for i, value in enumerate(parts):
        col_name = chr(65 + i)   # A, B, C...
        row[col_name] = value

    data.append(row)

df = pd.DataFrame(data)

# Fill missing columns (important)
df = df.fillna("")

print(df.head(10))
print("\nColumns:", df.columns.tolist())
print("\nTotal rows:", len(df))