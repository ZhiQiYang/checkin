# 替換 db/update_db.py 的內容
import sqlite3
import os
from config import Config

def update_database():
    """更新數據庫結構，重建表結構"""
    print("開始更新數據庫結構...")
    
    try:
        # 連接数据库 (如果不存在会创建)
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # 删除现有表并重建
        cursor.execute("DROP TABLE IF EXISTS checkin_records")
        cursor.execute("DROP TABLE IF EXISTS group_messages")
        
        # 创建打卡记录表
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
        
        # 创建群组消息表
        cursor.execute('''
        CREATE TABLE group_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            user_name TEXT NOT NULL,
            message TEXT,
            timestamp TEXT NOT NULL
        )
        ''')
        
        # 提交变更
        conn.commit()
        print("✅ 數據庫更新成功！重建了所有必要的表")
        
        conn.close()
        print("\n數據庫連接已關閉")
        
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")

if __name__ == "__main__":
    update_database()
