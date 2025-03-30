# db/update_db.py
import sqlite3
import os
from config import Config

def update_database():
    """完全重建數據庫結構"""
    print("開始更新數據庫結構...")
    
    try:
        # 如果數據庫文件存在，先刪除它
        if os.path.exists(Config.DB_PATH):
            os.remove(Config.DB_PATH)
            print("已刪除舊數據庫文件")
        
        # 創建新數據庫
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # 創建打卡記錄表
        cursor.execute('''
        CREATE TABLE checkin_records (
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
        
        # 創建群組消息表
        cursor.execute('''
        CREATE TABLE group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            message TEXT,
            timestamp TEXT NOT NULL
        )
        ''')
        
        conn.commit()
        print("✅ 數據庫更新成功！創建了所有必要的表")
        
        conn.close()
        print("數據庫連接已關閉")
        
    except Exception as e:
        print(f"❌ 更新數據庫時出錯: {e}")
