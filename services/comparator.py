import pandas as pd


def compare_data(txt_df, excel_df):

    txt = txt_df[[
        "deposit_slip_no",
        "txt_amount",
        "txt_station",
        "txt_date"
    ]]
    # print("txt_df", txt_df)

    excel = excel_df[[
        "deposit_slip_no",
        "excel_amount",
        "excel_station",
        "excel_area",
        "excel_date"
    ]]

    merged = pd.merge(
        txt,
        excel,
        on="deposit_slip_no",
        how="outer"
    )
    excel.to_excel("output.xlsx", sheet_name='Sheet1', index=False)
    txt.to_excel("output.xlsx", sheet_name='Sheet2', index=False)
    print("excel", excel)
    print("txt", txt)
    # -------------------------
    # STATE + DIFFERENCE
    # -------------------------
    def compute(row):
        txt_amt = row["txt_amount"]
        excel_amt = row["excel_amount"]

        if pd.notna(txt_amt) and pd.notna(excel_amt):
            diff = txt_amt - excel_amt
            state = "MATCHED" if diff == 0 else "MISMATCH"
        elif pd.notna(txt_amt):
            diff = None
            state = "UNMATCHED_TXT"
        else:
            diff = None
            state = "UNMATCHED_EXCEL"

        return pd.Series([diff, state])

    merged[["difference", "state"]] = merged.apply(compute, axis=1)
    merged.to_excel("output.xlsx", sheet_name='Sheet3', index=False)
    print(merged)
    return merged