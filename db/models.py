import sqlite3
from datetime import datetime

def save_checkin(user_id, name, location, note=None, latitude=None, longitude=None):
    conn = sqlite3.connect('checkins.db')
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")

    c.execute('''SELECT COUNT(*) FROM checkins WHERE user_id=? AND date=?''', (user_id, today))
    if c.fetchone()[0] > 0:
        return False, "今天已經打卡過了"

    c.execute('''
        INSERT INTO checkins (user_id, name, date, time, location, note, latitude, longitude)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (user_id, name, today, datetime.now().strftime("%H:%M:%S"), location, note, latitude, longitude))

    conn.commit()
    conn.close()
    return True, "打卡成功"
