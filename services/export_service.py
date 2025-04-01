# services/export_service.py
import pandas as pd
from datetime import datetime
import os
import sqlite3
import io
from config import Config
from flask import current_app
import time
import json

# 嘗試導入 reportlab，如果失敗則設置標誌
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: ReportLab not available. PDF export will be disabled.")

# 嘗試導入 Google API 相關包，如果失敗則設置標誌
try:
    from googleapiclient.discovery import build
    from google.oauth2 import service_account
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("Warning: Google API packages not available. Google Sheets export will be disabled.")

# 原有的 Excel 導出功能
def export_checkin_records_to_excel(user_id, date_from=None, date_to=None):
    # 從數據庫獲取打卡記錄
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    query_params = [user_id]
    query = '''
        SELECT cr.id, cr.user_id, cr.name, cr.location, cr.note, 
               cr.latitude, cr.longitude, cr.date, cr.time, cr.checkin_type
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
    
    # 將結果轉換為 DataFrame
    records = []
    for row in results:
        record = {}
        for key in row.keys():
            record[key] = row[key]
        records.append(record)
    
    df = pd.DataFrame(records)
    
    # 重命名欄位
    column_mapping = {
        'id': '序號',
        'user_id': '用戶ID',
        'name': '姓名',
        'location': '位置',
        'note': '備註',
        'latitude': '緯度',
        'longitude': '經度',
        'date': '日期',
        'time': '時間',
        'checkin_type': '打卡類型'
    }
    df = df.rename(columns=column_mapping)
    
    # 創建 Excel 文件
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='打卡記錄', index=False)
    
    output.seek(0)
    return output

# 新增 PDF 導出功能
def export_checkin_records_to_pdf(user_id, date_from=None, date_to=None):
    # 如果 ReportLab 不可用，返回 None
    if not REPORTLAB_AVAILABLE:
        return None

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
    # 如果 Google API 不可用，返回錯誤信息
    if not GOOGLE_API_AVAILABLE:
        return {'success': False, 'message': 'Google API 套件未安裝，無法使用 Google Sheets 匯出功能'}

    try:
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
