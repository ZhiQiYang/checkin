import pandas as pd
from flask import send_file
from io import BytesIO
from db import get_all_checkins

def export_checkin_excel():
    # 從資料庫取得所有紀錄
    rows = get_all_checkins()

    # 定義欄位名稱（與 db.py 對應）
    columns = [
        "ID", "User ID", "Name", "Date", "Time",
        "Location", "Note", "Latitude", "Longitude"
    ]

    # 將資料轉為 DataFrame
    df = pd.DataFrame(rows, columns=columns)

    # 建立記憶體內的 Excel 檔案
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='打卡紀錄')

    output.seek(0)

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name='打卡紀錄.xlsx',
        as_attachment=True
    )
