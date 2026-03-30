from flask import Flask, request, jsonify
from services.parser import parse_txt, parse_excel
from services.comparator import compare_data
# from services.db_service import upsert_records
from werkzeug.datastructures import FileStorage

app = Flask(__name__)


@app.route("/upload", methods=["POST"])
def upload():

    # txt_file = request.files["txt"]
    # excel_file = request.files["excel"]

    txt_path=r"C:\Users\cynix\Desktop\doorstep-banking\RAIL_SHAKTI_EXTRACT_17032026.txt"
    excel_path=r"C:\Users\cynix\Downloads\NWR_HCM (2).xls"

    # Convert file path → FileStorage (like Flask upload)
    txt_file = FileStorage(
        stream=open(txt_path, "rb"),
        filename="file.txt"
    )

    excel_file = FileStorage(
        stream=open(excel_path, "rb"),
        filename="file.xls"
    )
    txt_df = parse_txt(txt_file)
    excel_df = parse_excel(excel_file)
    
    merged_df = compare_data(txt_df, excel_df)

    # upsert_records(merged_df)

    return jsonify({
        "message": "Processed successfully",
        "records": len(merged_df)
    })


if __name__ == "__main__":
    app.run(debug=True)