from sqlalchemy import text
from config.database import engine
import pandas as pd


def upsert_records(df):
    with engine.begin() as conn:

        for _, row in df.iterrows():

            # -------------------------
            # VALIDATION
            # -------------------------
            deposit_slip_no = str(row.get("deposit_slip_no", "")).strip()
            if (not deposit_slip_no) or (deposit_slip_no == 0):
                continue  # skip invalid rows

            # -------------------------
            # DATE CONVERSION (IMPORTANT)
            # -------------------------
            txt_date = row.get("txt_date")
            excel_date = row.get("excel_date")

            if pd.notna(txt_date):
                txt_date = txt_date.date()
            else:
                txt_date = None

            if pd.notna(excel_date):
                excel_date = excel_date.date()
            else:
                excel_date = None

            # -------------------------
            # SQL MERGE QUERY
            # -------------------------
            query = text("""
            MERGE reconciliation_records AS target
            USING (SELECT :deposit_slip_no AS deposit_slip_no) AS source
            ON target.deposit_slip_no = source.deposit_slip_no

            WHEN MATCHED THEN
                UPDATE SET
                    txt_amount = COALESCE(:txt_amount, target.txt_amount),
                    excel_amount = COALESCE(:excel_amount, target.excel_amount),
                    difference = :difference,
                    txt_station = COALESCE(:txt_station, target.txt_station),
                    excel_station = COALESCE(:excel_station, target.excel_station),
                    excel_area = COALESCE(:excel_area, target.excel_area),
                    txt_date = COALESCE(:txt_date, target.txt_date),
                    excel_date = COALESCE(:excel_date, target.excel_date),
                    state = :state,
                    last_updated_date = GETDATE(),
                    matched_date = CASE 
                        WHEN :state IN ('MATCHED','MISMATCH') THEN GETDATE()
                        ELSE target.matched_date
                    END

            WHEN NOT MATCHED THEN
                INSERT (
                    deposit_slip_no,
                    txt_amount,
                    excel_amount,
                    difference,
                    txt_station,
                    excel_station,
                    excel_area,
                    txt_date,
                    excel_date,
                    state,
                    first_seen_date,
                    last_updated_date,
                    matched_date
                )
                VALUES (
                    :deposit_slip_no,
                    :txt_amount,
                    :excel_amount,
                    :difference,
                    :txt_station,
                    :excel_station,
                    :excel_area,
                    :txt_date,
                    :excel_date,
                    :state,
                    GETDATE(),
                    GETDATE(),
                    CASE 
                        WHEN :state IN ('MATCHED','MISMATCH') THEN GETDATE()
                        ELSE NULL
                    END
                );
            """)

            # -------------------------
            # EXECUTE QUERY
            # -------------------------
            conn.execute(query, {
                "deposit_slip_no": deposit_slip_no,
                "txt_amount": row.get("txt_amount"),
                "excel_amount": row.get("excel_amount"),
                "difference": row.get("difference"),
                "txt_station": row.get("txt_station"),
                "excel_station": row.get("excel_station"),
                "excel_area": row.get("excel_area"),
                "txt_date": txt_date,
                "excel_date": excel_date,
                "state": row.get("state")
            })