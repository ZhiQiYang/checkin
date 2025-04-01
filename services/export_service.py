# services/export_service.py
import pandas as pd
from datetime import datetime
import os
import sqlite3
import io
from config import Config
from flask import current_app
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import time
import json

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

# 新增 PDF 導出功能
def export_checkin_records_to_pdf(user_id, date_from=None, date_to=None):
    # 從數據庫獲取打卡記錄
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query_params = [user_id]
    query = '''
        SELECT cr.id, cr.name, cr.location, cr.note, 
               cr.date, cr.time, cr.checkin_type
        FROM checkin_records cr
        WHERE cr.user_id = ?
    '''
    
    if date_from:
        query += ' AND cr.date >= ?'
        query_params.append(date_from)
    
    if date_to:
        query += ' AND cr.date <= ?'
        query_params.append(date_to)
    
    query += ' ORDER BY cr.date DESC, cr.time DESC'
    
    c.execute(query, query_params)
    results = c.fetchall()
    conn.close()
    
    if not results:
        return None
    
    # 準備 PDF 數據
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    
    # 添加標題
    styles = getSampleStyleSheet()
    elements.append(Paragraph(f"打卡記錄 - 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Title']))
    
    # 表格列頭
    column_names = ['序號', '姓名', '位置', '備註', '日期', '時間', '打卡類型']
    
    # 表格數據
    data = [column_names]
    for row in results:
        data.append([
            row['id'],
            row['name'],
            row['location'],
            row['note'],
            row['date'],
            row['time'],
            row['checkin_type']
        ])
    
    # 創建表格
    table = Table(data)
    
    # 設置表格樣式
    table_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ])
    table.setStyle(table_style)
    
    elements.append(table)
    
    # 生成 PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

# 新增 Google Sheets 導出準備功能
def prepare_google_sheets_export(user_id, date_from=None, date_to=None):
    # 從數據庫獲取打卡記錄
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query_params = [user_id]
    query = '''
        SELECT cr.id, cr.name, cr.location, cr.note, 
               cr.date, cr.time, cr.checkin_type
        FROM checkin_records cr
        WHERE cr.user_id = ?
    '''
    
    if date_from:
        query += ' AND cr.date >= ?'
        query_params.append(date_from)
    
    if date_to:
        query += ' AND cr.date <= ?'
        query_params.append(date_to)
    
    query += ' ORDER BY cr.date DESC, cr.time DESC'
    
    c.execute(query, query_params)
    results = c.fetchall()
    conn.close()
    
    if not results:
        return None
    
    # 準備數據為 Google Sheets 適用的格式
    sheets_data = {
        'header': ['序號', '姓名', '位置', '備註', '日期', '時間', '打卡類型'],
        'values': []
    }
    
    for row in results:
        sheets_data['values'].append([
            row['id'],
            row['name'],
            row['location'],
            row['note'],
            row['date'],
            row['time'],
            row['checkin_type']
        ])
    
    return sheets_data

# 新增生成 Google Sheets 的函數（可選，如果您要在後端直接生成）
def create_google_sheets_export(data, title=None):
    """
    使用 Google Sheets API 創建一個新的 Sheet
    需要設置 Google API 憑證和權限
    
    注意：這個功能需要在服務器上配置 Google API 憑證
    """
    try:
        from googleapiclient.discovery import build
        from google.oauth2 import service_account
        
        # 檢查憑證文件是否存在
        credentials_path = os.environ.get('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
        if not os.path.exists(credentials_path):
            return {'success': False, 'message': 'Google API 憑證文件不存在'}
        
        # 設置 API 範圍和身份驗證
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path, scopes=SCOPES)
        
        service = build('sheets', 'v4', credentials=credentials)
        
        # 創建新的電子表格
        sheet_title = title or f"打卡記錄 {datetime.now().strftime('%Y-%m-%d')}"
        spreadsheet = {
            'properties': {
                'title': sheet_title
            }
        }
        
        spreadsheet = service.spreadsheets().create(body=spreadsheet).execute()
        
        # 填充數據
        sheet_id = spreadsheet.get('spreadsheetId')
        header_range = 'Sheet1!A1:G1'
        values_range = f"Sheet1!A2:G{len(data['values'])+1}"
        
        # 新增列頭
        header_body = {
            'values': [data['header']]
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=header_range,
            valueInputOption='RAW',
            body=header_body
        ).execute()
        
        # 新增數據
        values_body = {
            'values': data['values']
        }
        
        service.spreadsheets().values().update(
            spreadsheetId=sheet_id,
            range=values_range,
            valueInputOption='RAW',
            body=values_body
        ).execute()
        
        # 格式化列頭
        requests = [{
            'updateCells': {
                'rows': {
                    'values': [{
                        'userEnteredFormat': {
                            'backgroundColor': {
                                'red': 0.5,
                                'green': 0.5,
                                'blue': 0.5
                            },
                            'textFormat': {
                                'bold': True
                            }
                        }
                    }]
                },
                'fields': 'userEnteredFormat(backgroundColor,textFormat)',
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1
                }
            }
        }]
        
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body={'requests': requests}
        ).execute()
        
        # 返回結果
        sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        return {
            'success': True, 
            'spreadsheetId': sheet_id, 
            'spreadsheetUrl': sheet_url
        }
    except Exception as e:
        return {'success': False, 'message': str(e)}
