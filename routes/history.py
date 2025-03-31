from flask import Blueprint, request, render_template
from datetime import datetime, timedelta
from config import Config
import sqlite3
from utils.timezone import get_current_time

history_bp = Blueprint('history', __name__)

@history_bp.route('/personal-history')
def personal_history():
    user_id = request.args.get('userId')
    if not user_id:
        return "請從 LINE 應用程式訪問此頁面", 400

    days_filter = request.args.get('dateRange', '7')
    
    # 從數據庫獲取打卡記錄
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if days_filter == 'all':
        c.execute('''
            SELECT * FROM checkin_records 
            WHERE user_id = ? 
            ORDER BY date DESC, time DESC
        ''', (user_id,))
    else:
        # 計算日期範圍
        days = int(days_filter)
        now = get_current_time()
        date_limit = (now - timedelta(days=days)).strftime('%Y-%m-%d')
        
        c.execute('''
            SELECT * FROM checkin_records 
            WHERE user_id = ? AND date >= ? 
            ORDER BY date DESC, time DESC
        ''', (user_id, date_limit))
    
    results = c.fetchall()
    conn.close()
    
    # 轉換為模板可用的記錄格式
    records = []
    for row in results:
        record = dict(row)
        
        # 處理經緯度（如果有）
        if row['latitude'] and row['longitude']:
            record['coordinates'] = {
                'latitude': row['latitude'],
                'longitude': row['longitude']
            }
        
        records.append(record)
    
    # 檢查是否有帶地圖的記錄
    has_map_records = any(record.get('coordinates') for record in records)
    
    return render_template('personal_history.html', 
                          records=records, 
                          days=days_filter,
                          has_map_records=has_map_records,
                          google_maps_api_key=Config.GOOGLE_MAPS_API_KEY)
