import pandas as pd
import tempfile


def parse_txt(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
        file.save(tmp.name)
        path = tmp.name

    colspecs = [
        (0, 9), (9, 20), (20, 56), (56, 86), (86, 108),
        (108, 123), (123, 139), (139, 165),
        (165, 170), (170, 180), (180, 196)
    ]

    col_names = list("ABCDEFGHIJK")

    df = pd.read_fwf(path, colspecs=colspecs, names=col_names)

    # Keep valid rows
    df = df[df["A"].astype(str).str.strip().str.match(r"^\d+", na=False)]

    df = df.apply(lambda x: x.astype(str).str.strip())

    # -------------------------
    # AMOUNT
    # -------------------------
    df["txt_amount"] = pd.to_numeric(
        df["C"].str.replace(",", ""),
        errors="coerce"
    )
    df = df.dropna(subset=["txt_amount"])

    # -------------------------
    # CORE FIELDS
    # -------------------------
    df["deposit_slip_no"] = df["B"]
    df["txt_station"] = df["E"]
    # print(df["J"].head(10).tolist())
    # ✅ FIX: Convert TXT date (DDMMYYYY → datetime)
    df["txt_date"] = pd.to_datetime(
        df["J"].astype(str).str.replace(".0", "", regex=False).str.strip(),
        format="%d%m%Y",
        errors="coerce"
    )
    # print("TXT Date:", df["txt_date"])
    # print(df)
    return df


def parse_excel(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xls") as tmp:
        file.save(tmp.name)
        path = tmp.name

    df = pd.read_csv(path, encoding="utf-16", sep=";", skiprows=1)

    df.columns = df.columns.str.strip().str.lower()

    # -------------------------
    # AMOUNT
    # -------------------------
    df["excel_amount"] = pd.to_numeric(
        df["cash_pickup_amt"],
        errors="coerce"
    )

    # -------------------------
    # CORE FIELDS
    # -------------------------
    df["deposit_slip_no"] = df["deposit_slip_no"]
    df["excel_station"] = df["station_code"]
    df["excel_area"] = df["area"]

    # ✅ FIX: correct column + convert to datetime
    df["excel_date"] = pd.to_datetime(
        df["pickupdate"],
        errors="coerce"
    )
    # print(df)
    df=df.head(10)
    return df