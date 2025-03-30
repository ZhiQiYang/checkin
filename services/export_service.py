# services/export_service.py
import pandas as pd
from datetime import datetime
import os
import sqlite3
from config import Config

def export_checkin_records_to_excel(user_id=None, date_from=None, date_to=None):
    """
    匯出打卡記錄到 Excel 檔案
    
    參數:
    - user_id: 指定用戶的ID，如果為None則匯出所有用戶
    - date_from: 開始日期，格式 YYYY-MM-DD
    - date_to: 結束日期，格式 YYYY-MM-DD
    
    返回:
    - 生成的Excel檔案路徑
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
    
    # 確保存儲目錄存在
    if not os.path.exists('exports'):
        os.makedirs('exports')
    
    # 生成檔案名稱
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"exports/checkin_records_{timestamp}.xlsx"
    
    # 使用上下文管理器寫入Excel (修改這部分)
    with pd.ExcelWriter(filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='打卡記錄')
    
    # 自動調整列寬
    worksheet = writer.sheets['打卡記錄']
    for i, col in enumerate(df.columns):
        max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2
        worksheet.column_dimensions[chr(65 + i)].width = max_length
    
    writer.close()
    
    return filename
