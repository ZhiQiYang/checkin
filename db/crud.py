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
    
    # 建立用戶表
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            display_name TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
        
        # 簡化查詢，不使用 checkin_type
        c.execute('SELECT * FROM checkin_records WHERE user_id = ? AND date = ?', 
                (user_id, today))
        
        if c.fetchone():
            conn.close()
            return False, f"今天已經打卡過了"

        now = datetime.now()
        time_str = now.strftime('%H:%M:%S')

        # 插入新紀錄
        c.execute('''
            INSERT INTO checkin_records (user_id, name, location, note, latitude, longitude, date, time, checkin_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, name, location, note, latitude, longitude, today, time_str, checkin_type))

        conn.commit()
        conn.close()
        return True, f"{checkin_type}打卡成功"
    except Exception as e:
        print(f"保存打卡記錄錯誤: {str(e)}")
        return False, f"數據庫錯誤: {str(e)}"

# 在 db/crud.py 中添加
def create_reminder_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 提醒設置表
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminder_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            enabled BOOLEAN DEFAULT 1,
            morning_time TEXT DEFAULT '09:00',  # 上班提醒時間
            evening_time TEXT DEFAULT '18:00',  # 下班提醒時間
            weekend_enabled BOOLEAN DEFAULT 0,  # 是否在周末提醒
            holiday_enabled BOOLEAN DEFAULT 0,  # 是否在節假日提醒
            created_at DATETIME,
            updated_at DATETIME,
            UNIQUE(user_id)
        )
    ''')
    
    # 提醒日誌表
    c.execute('''
        CREATE TABLE IF NOT EXISTS reminder_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            reminder_type TEXT NOT NULL,  # morning/evening
            sent_at DATETIME,
            status TEXT  # sent/delivered/read
        )
    ''')
    
    conn.commit()
    conn.close()

# 在 db/crud.py 中添加

def get_reminder_setting(user_id):
    """獲取用戶的提醒設置"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('SELECT * FROM reminder_settings WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    
    if not row:
        # 默認設置
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''
            INSERT INTO reminder_settings 
            (user_id, created_at, updated_at) 
            VALUES (?, ?, ?)
        ''', (user_id, now, now))
        conn.commit()
        
        c.execute('SELECT * FROM reminder_settings WHERE user_id = ?', (user_id,))
        row = c.fetchone()
    
    setting = dict(row) if row else None
    conn.close()
    return setting

def update_reminder_setting(user_id, settings):
    """更新用戶的提醒設置"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    fields = []
    values = []
    
    for key, value in settings.items():
        if key in ['enabled', 'morning_time', 'evening_time', 
                  'weekend_enabled', 'holiday_enabled']:
            fields.append(f"{key} = ?")
            values.append(value)
    
    if not fields:
        conn.close()
        return False
    
    fields.append("updated_at = ?")
    values.append(now)
    values.append(user_id)
    
    query = f'''
        UPDATE reminder_settings
        SET {", ".join(fields)}
        WHERE user_id = ?
    '''
    
    c.execute(query, values)
    conn.commit()
    conn.close()
    return True

def log_reminder(user_id, reminder_type):
    """記錄已發送的提醒"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute('''
        INSERT INTO reminder_logs
        (user_id, reminder_type, sent_at, status)
        VALUES (?, ?, ?, ?)
    ''', (user_id, reminder_type, now, 'sent'))
    
    conn.commit()
    conn.close()

def get_users_needing_reminder(reminder_type):
    """獲取需要發送提醒的用戶列表"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    now = datetime.now()
    current_time = now.strftime('%H:%M')
    today = now.strftime('%Y-%m-%d')
    
    # 檢查是否為週末
    is_weekend = now.weekday() >= 5  # 5=Saturday, 6=Sunday
    
    # 獲取今天有特定類型提醒的用戶列表
    time_field = 'morning_time' if reminder_type == 'morning' else 'evening_time'
    
    c.execute(f'''
        SELECT r.user_id, r.{time_field}, u.name, u.display_name
        FROM reminder_settings r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.enabled = 1 
        AND r.{time_field} <= ?
        AND (r.weekend_enabled = 1 OR ? = 0)
    ''', (current_time, 1 if is_weekend else 0))
    
    potential_users = c.fetchall()
    users_to_remind = []
    
    for user in potential_users:
        # 檢查今天是否已經打卡（上班提醒）或（下班提醒）
        checkin_type = 'morning' if reminder_type == 'morning' else 'evening'
        
        c.execute('''
            SELECT * FROM checkin_records
            WHERE user_id = ? AND date = ? AND checkin_type = ?
        ''', (user['user_id'], today, checkin_type))
        
        if c.fetchone() is None:
            # 檢查今天是否已經發送過提醒
            c.execute('''
                SELECT * FROM reminder_logs
                WHERE user_id = ? AND reminder_type = ? AND DATE(sent_at) = ?
            ''', (user['user_id'], reminder_type, today))
            
            if c.fetchone() is None:
                users_to_remind.append({
                    'user_id': user['user_id'],
                    'name': user['name'] or user['display_name'],
                    'reminder_time': user[time_field]
                })
    
    conn.close()
    return users_to_remind
