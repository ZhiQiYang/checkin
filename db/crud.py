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
            time TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def save_checkin(user_id, name, location, note=None, latitude=None, longitude=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 取得今天日期
    today = datetime.now().strftime('%Y-%m-%d')

    # 檢查是否已打卡
    c.execute('SELECT * FROM checkin_records WHERE user_id = ? AND date = ?', (user_id, today))
    if c.fetchone():
        conn.close()
        return False, "今天已經打卡過了"

    now = datetime.now()
    time_str = now.strftime('%H:%M:%S')

    # 插入新紀錄
    c.execute('''
        INSERT INTO checkin_records (user_id, name, location, note, latitude, longitude, date, time)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, location, note, latitude, longitude, today, time_str))

    conn.commit()
    conn.close()
    return True, "打卡成功"
