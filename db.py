import sqlite3
from datetime import datetime

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'checkin.db')


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS checkin_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            location TEXT,
            note TEXT,
            latitude REAL,
            longitude REAL
        )
    ''')
    conn.commit()
    conn.close()

def save_checkin(user_id, name, location, note=None, latitude=None, longitude=None):
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M:%S")

    if has_checked_in_today(user_id, date_str):
        return False, "今天已經打卡過了"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO checkin_records (user_id, name, date, time, location, note, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, date_str, time_str, location, note, latitude, longitude))
    conn.commit()
    conn.close()
    return True, "打卡成功"

def has_checked_in_today(user_id, date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM checkin_records WHERE user_id = ? AND date = ?
    ''', (user_id, date_str))
    result = cursor.fetchone()[0]
    conn.close()
    return result > 0

def get_all_checkins():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM checkin_records ORDER BY date DESC, time DESC''')
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_checkins_by_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''SELECT * FROM checkin_records WHERE user_id = ? ORDER BY date DESC, time DESC''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows
