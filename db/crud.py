# db/crud.py

import sqlite3
from datetime import datetime

DB_PATH = 'checkin.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 建立打卡紀錄表格
    c.execute('''
        CREATE TABLE IF NOT EXISTS checkin_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            location TEXT,
            note TEXT,
            latitude REAL,
            longitude REAL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            checkin_type TEXT DEFAULT '上班'
        )
    ''')
    
    # 建立群組訊息表格
    c.execute('''
        CREATE TABLE IF NOT EXISTS group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            message TEXT,
            timestamp TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def save_group_message(user_id, user_name, message, timestamp):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO group_messages (user_id, user_name, message, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, user_name, message, timestamp))
    conn.commit()
    conn.close()

def get_recent_messages(count=20):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT * FROM group_messages 
        ORDER BY id DESC LIMIT ?
    ''', (count,))
    results = c.fetchall()
    conn.close()
    
    # 轉換為字典列表
    messages = []
    for row in results:
        messages.append({
            "user_id": row["user_id"],
            "user_name": row["user_name"],
            "message": row["message"],
            "timestamp": row["timestamp"]
        })
    return messages

def save_checkin(user_id, name, location, note=None, latitude=None, longitude=None, checkin_type="上班"):
    """保存打卡記錄到數據庫"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # 取得今天日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 簡化查詢條件，只檢查用戶和日期
        c.execute('SELECT * FROM checkin_records WHERE user_id = ? AND date = ?', 
                (user_id, today))
        
        if c.fetchone():
            conn.close()
            return False, f"今天已經打卡過了"

        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')

        # 檢查表格是否有 checkin_type 欄位
        c.execute("PRAGMA table_info(checkin_records)")
        columns = [col[1] for col in c.fetchall()]
        
        if "checkin_type" in columns:
            # 有 checkin_type 欄位，使用完整 SQL
            c.execute('''
                INSERT INTO checkin_records (user_id, name, location, note, latitude, longitude, date, time, checkin_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, location, note, latitude, longitude, today, time_str, checkin_type))
        else:
            # 沒有 checkin_type 欄位，使用簡化 SQL
            c.execute('''
                INSERT INTO checkin_records (user_id, name, location, note, latitude, longitude, date, time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, location, note, latitude, longitude, today, time_str))

        conn.commit()
        conn.close()
        return True, f"{checkin_type}打卡成功"
    except Exception as e:
        print(f"保存打卡記錄錯誤: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False, f"數據庫錯誤: {str(e)}"
