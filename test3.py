import pandas as pd

file_path = r"C:\Users\cynix\Desktop\doorstep-banking\RAIL_SHAKTI_EXTRACT_17032026.txt"

# Updated column specs
colspecs = [
    (0, 9),     # A
    (9, 20),    # B
    (20, 56),    # C → amount
    (56, 86),    # D
    (86, 108),   # E → station
    (108, 123),  # F
    (123, 139),  # G
    (139, 165),  # H
    (165, 170),  # I
    (170, 180),  # J → date
    (180, 196)   # K → account
]

# Column names
col_names = list("ABCDEFGHIJK")

df = pd.read_fwf(
    file_path,
    colspecs=colspecs,
    names=col_names
)

# Filter valid transaction rows
df = df[df["A"].str.strip().str.match(r"^\d+", na=False)]

# Clean spaces
df = df.apply(lambda x: x.astype(str).str.strip())

# Convert amount safely
df["amount"] = pd.to_numeric(
    df["C"].str.replace(",", ""),
    errors="coerce"
)

df = df.dropna(subset=["amount"])

# Useful fields
df["station"] = df["E"]
df["date"] = df["J"]
df["account"] = df["K"]

# Show output
print(df.head(10).to_string())
print("\nColumns:", df.columns.tolist())
print("\nTotal rows:", len(df))