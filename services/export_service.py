# services/export_service.py
import pandas as pd
from datetime import datetime
import os
import sqlite3
import io
from config import Config

# 修改 services/export_service.py

def export_checkin_records_to_excel(user_id=None, date_from=None, date_to=None):
    """
    匯出打卡記錄到 Excel 缓冲區
    """
    conn = sqlite3.connect(Config.DB_PATH)
    
    # 構建SQL查詢
    query = "SELECT * FROM checkin_records"
    params = []
    
    conditions = []
    if user_id:
        conditions.append("user_id = ?")
        params.append(user_id)
    
    if date_from:
        conditions.append("date >= ?")
        params.append(date_from)
    
    if date_to:
        conditions.append("date <= ?")
        params.append(date_to)
    
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY date DESC, time DESC"
    
    # 讀取數據
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    
    if df.empty:
        return None
    
    # 使用BytesIO而不是文件
    output = io.BytesIO()
    
    # 寫入Excel到內存緩衝區
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='打卡記錄')
        
        # 自動調整列寬
        worksheet = writer.sheets['打卡記錄']
        for i, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + i)].width = max_length
    
    # 將指針移動到開頭
    output.seek(0)
    
    return output
