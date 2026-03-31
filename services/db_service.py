from sqlalchemy import text
from config.database import engine
import pandas as pd


def clean_value(val):
    if pd.isna(val):
        return None
    return val


def upsert_records(df):
    with engine.begin() as conn:
        print("reached the upsert record function")

        for _, row in df.head(100).iterrows():

            # -------------------------
            # VALIDATION
            # -------------------------
            deposit_slip_no = str(row.get("deposit_slip_no", "")).strip()
            if not deposit_slip_no or deposit_slip_no == "0":
                continue

            # -------------------------
            # DATE CONVERSION
            # -------------------------
            txt_date = row.get("txt_date")
            excel_date = row.get("excel_date")

            txt_date = txt_date.date() if pd.notna(txt_date) else None
            excel_date = excel_date.date() if pd.notna(excel_date) else None

            # -------------------------
            # SQL MERGE QUERY (FIXED)
            # -------------------------
            query = text("""
            MERGE reconciliation_records AS target
            USING (VALUES (:deposit_slip_no)) AS source(deposit_slip_no)
            ON target.deposit_slip_no = source.deposit_slip_no

            WHEN MATCHED THEN
                UPDATE SET

                    txt_amount = COALESCE(:txt_amount, target.txt_amount),
                    excel_amount = COALESCE(:excel_amount, target.excel_amount),

                    -- ✅ DIFFERENCE (FIXED)
                    difference = 
                        CASE 
                            WHEN COALESCE(:txt_amount, target.txt_amount) IS NOT NULL
                             AND COALESCE(:excel_amount, target.excel_amount) IS NOT NULL
                            THEN COALESCE(:txt_amount, target.txt_amount) 
                                 - COALESCE(:excel_amount, target.excel_amount)
                            ELSE NULL
                        END,

                    txt_station = COALESCE(:txt_station, target.txt_station),
                    excel_station = COALESCE(:excel_station, target.excel_station),
                    excel_area = COALESCE(:excel_area, target.excel_area),

                    txt_date = COALESCE(:txt_date, target.txt_date),
                    excel_date = COALESCE(:excel_date, target.excel_date),

                    -- ✅ STATE (FIXED)
                    state = 
                        CASE 
                            WHEN COALESCE(:txt_amount, target.txt_amount) IS NOT NULL
                             AND COALESCE(:excel_amount, target.excel_amount) IS NOT NULL
                            THEN 
                                CASE 
                                    WHEN COALESCE(:txt_amount, target.txt_amount) 
                                         = COALESCE(:excel_amount, target.excel_amount)
                                    THEN 'MATCHED'
                                    ELSE 'MISMATCH'
                                END

                            WHEN COALESCE(:txt_amount, target.txt_amount) IS NOT NULL
                            THEN 'UNMATCHED_TXT'

                            ELSE 'UNMATCHED_EXCEL'
                        END,

                    last_updated_date = GETDATE(),

                    matched_date = CASE 
                        WHEN COALESCE(:txt_amount, target.txt_amount) IS NOT NULL
                         AND COALESCE(:excel_amount, target.excel_amount) IS NOT NULL
                        THEN GETDATE()
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

                    -- ✅ DIFFERENCE
                    CASE 
                        WHEN :txt_amount IS NOT NULL AND :excel_amount IS NOT NULL
                        THEN :txt_amount - :excel_amount
                        ELSE NULL
                    END,

                    :txt_station,
                    :excel_station,
                    :excel_area,
                    :txt_date,
                    :excel_date,

                    -- ✅ STATE
                    CASE 
                        WHEN :txt_amount IS NOT NULL AND :excel_amount IS NOT NULL
                        THEN 
                            CASE 
                                WHEN :txt_amount = :excel_amount THEN 'MATCHED'
                                ELSE 'MISMATCH'
                            END
                        WHEN :txt_amount IS NOT NULL THEN 'UNMATCHED_TXT'
                        ELSE 'UNMATCHED_EXCEL'
                    END,

                    GETDATE(),
                    GETDATE(),

                    CASE 
                        WHEN :txt_amount IS NOT NULL AND :excel_amount IS NOT NULL
                        THEN GETDATE()
                        ELSE NULL
                    END
                );
            """)

            print(deposit_slip_no, row.get("state"))

            try:
                conn.execute(query, {
                    "deposit_slip_no": deposit_slip_no,
                    "txt_amount": clean_value(row.get("txt_amount")),
                    "excel_amount": clean_value(row.get("excel_amount")),
                    "txt_station": clean_value(row.get("txt_station")),
                    "excel_station": clean_value(row.get("excel_station")),
                    "excel_area": clean_value(row.get("excel_area")),
                    "txt_date": txt_date,
                    "excel_date": excel_date
                })
                print("✅ SUCCESS:", deposit_slip_no)

            except Exception as e:
                print("❌ FAILED:", deposit_slip_no)
                print("ERROR:", e)