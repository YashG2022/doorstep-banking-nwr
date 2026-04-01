from flask import Flask, request, jsonify, render_template
from services.parser import parse_txt, parse_excel
from services.comparator import compare_data
from services.db_service import upsert_records, execute_query
from werkzeug.datastructures import FileStorage
from flask import send_file
from sqlalchemy import text
import pandas as pd
import io

app = Flask(__name__)


# @app.route("/upload", methods=["POST"])
# def upload():

#     # txt_file = request.files["txt"]
#     # excel_file = request.files["excel"]

#     txt_path=r"C:\Users\yashg\Desktop\DMT\doorstep-banking\doorstep-banking-nwr\test.txt"
#     excel_path=r"C:\Users\yashg\Desktop\DMT\doorstep-banking\doorstep-banking-nwr\NWR_HCM.xls"

#     # Convert file path → FileStorage (like Flask upload)
#     txt_file = FileStorage(
#         stream=open(txt_path, "rb"),
#         filename="file.txt"
#     )

#     excel_file = FileStorage(
#         stream=open(excel_path, "rb"),
#         filename="file.xls"
#     )
#     txt_df = parse_txt(txt_file)
#     excel_df = parse_excel(excel_file)
    
#     merged_df = compare_data(txt_df, excel_df)

#     upsert_records(merged_df)

#     return jsonify({
#         "message": "Processed successfully",
#         "records": len(merged_df)
#     })

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():

    txt_file = request.files["txt"]
    excel_file = request.files["excel"]

    txt_df = parse_txt(txt_file)
    excel_df = parse_excel(excel_file)

    merged_df = compare_data(txt_df, excel_df)

    upsert_records(merged_df)

    # Convert dataframe → list of dicts for HTML
    data = merged_df.fillna("").to_dict(orient="records")

    return render_template(
        "result.html",
        data=data,
        columns=merged_df.columns,
        records=len(merged_df)
    )


@app.route("/dashboard", methods=["GET"])
def dashboard():

    selected_range = request.args.get("range", "all")

    # -------------------------
    # CONDITION BASED QUERY
    # -------------------------
    if selected_range == "latest":
        condition = """
        WHERE CAST(last_updated_date AS DATE) = 
              (SELECT MAX(CAST(last_updated_date AS DATE)) FROM reconciliation_records)
        """

    elif selected_range == "30days":
        condition = """
        WHERE last_updated_date >= DATEADD(day, -30, GETDATE())
        """

    else:
        condition = ""  # lifetime

    # -------------------------
    # SUMMARY QUERY
    # -------------------------
    summary_query = text(f"""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN state = 'MATCHED' THEN 1 ELSE 0 END) as matched,
            SUM(CASE WHEN state = 'MISMATCH' THEN 1 ELSE 0 END) as mismatch,
            SUM(CASE WHEN state LIKE 'UNMATCHED%' THEN 1 ELSE 0 END) as unmatched,
            SUM(CASE WHEN state = 'MISMATCH' THEN difference ELSE 0 END) as mismatch_amount
        FROM reconciliation_records
        {condition}
    """)

    result = execute_query(summary_query, fetch_one=True)

    summary = {
        "total": result.total or 0,
        "matched": result.matched or 0,
        "mismatch": result.mismatch or 0,
        "unmatched": result.unmatched or 0,
        "mismatch_amount": result.mismatch_amount or 0
    }

    return render_template(
        "dashboard.html",
        summary=summary,
        selected_range=selected_range
    )

@app.route("/download", methods=["GET"])
def download():

    report_type = request.args.get("type")

    if report_type == "latest":
        query = text("""
            SELECT *
            FROM reconciliation_records
            WHERE CAST(last_updated_date AS DATE) = 
                  (SELECT MAX(CAST(last_updated_date AS DATE)) FROM reconciliation_records)
        """)

    elif report_type == "30days":
        query = text("""
            SELECT *
            FROM reconciliation_records
            WHERE last_updated_date >= DATEADD(day, -30, GETDATE())
        """)

    else:
        return "Invalid type", 400

    rows = execute_query(query)
    df = pd.DataFrame([dict(row._mapping) for row in rows])

    if df.empty:
        return "No data available", 404

    # -------------------------
    # SPLIT INTO SHEETS
    # -------------------------
    matched = df[df["state"] == "MATCHED"]
    mismatch = df[df["state"] == "MISMATCH"]
    unmatched_txt = df[df["state"] == "UNMATCHED_TXT"]
    unmatched_excel = df[df["state"] == "UNMATCHED_EXCEL"]

    # -------------------------
    # CREATE EXCEL IN MEMORY
    # -------------------------
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        matched.to_excel(writer, sheet_name="MATCHED", index=False)
        mismatch.to_excel(writer, sheet_name="MISMATCH", index=False)
        unmatched_txt.to_excel(writer, sheet_name="UNMATCHED_TXT", index=False)
        unmatched_excel.to_excel(writer, sheet_name="UNMATCHED_EXCEL", index=False)

    output.seek(0)

    return send_file(
        output,
        download_name="reconciliation_report.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

if __name__ == "__main__":
    app.run(debug=True)