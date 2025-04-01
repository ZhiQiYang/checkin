# db/update_db.py
import sqlite3
import os
from config import Config

def update_database():
    """檢查並更新數據庫結構，保留現有數據"""
    print("檢查數據庫結構...")
    
    try:
        # 檢查數據庫文件是否存在，如果不存在則創建
        if not os.path.exists(Config.DB_PATH):
            print("數據庫文件不存在，創建新數據庫...")
            conn = sqlite3.connect(Config.DB_PATH)
            conn.close()
            print("✅ 創建了新的數據庫文件")
            return  # 返回，讓 init_db() 處理表的創建
        
        # 連接到現有數據庫
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # 獲取現有表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"現有表: {existing_tables}")
        
        # 檢查各表結構，如有需要進行更新
        
        # 檢查並更新 checkin_records 表
        if 'checkin_records' in existing_tables:
            print("檢查 checkin_records 表結構...")
            cursor.execute("PRAGMA table_info(checkin_records)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 如果缺少 checkin_type 列，添加它
            if 'checkin_type' not in columns:
                print("添加 checkin_type 列到 checkin_records 表...")
                cursor.execute("ALTER TABLE checkin_records ADD COLUMN checkin_type TEXT DEFAULT '上班'")
                print("✅ 已添加 checkin_type 列")
        
        # 檢查 users 表，如果不存在則創建
        if 'users' not in existing_tables:
            print("創建 users 表...")
            cursor.execute('''
                CREATE TABLE users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    display_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ 已創建 users 表")
        
        # 檢查並創建提醒系統相關表
        if 'reminder_settings' not in existing_tables:
            print("創建 reminder_settings 表...")
            cursor.execute('''
                CREATE TABLE reminder_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    morning_time TEXT DEFAULT '09:00',
                    evening_time TEXT DEFAULT '18:00',
                    weekend_enabled BOOLEAN DEFAULT 0,
                    holiday_enabled BOOLEAN DEFAULT 0,
                    created_at DATETIME,
                    updated_at DATETIME,
                    UNIQUE(user_id)
                )
            ''')
            print("✅ 已創建 reminder_settings 表")
        
        if 'reminder_logs' not in existing_tables:
            print("創建 reminder_logs 表...")
            cursor.execute('''
                CREATE TABLE reminder_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    reminder_type TEXT NOT NULL,
                    sent_at DATETIME,
                    status TEXT
                )
            ''')
            print("✅ 已創建 reminder_logs 表")
        
        # 檢查並創建詞彙相關表
        if 'vocabulary' not in existing_tables:
            print("創建 vocabulary 表...")
            cursor.execute('''
                CREATE TABLE vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    english_word TEXT UNIQUE NOT NULL,
                    chinese_translation TEXT NOT NULL,
                    difficulty INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ 已創建 vocabulary 表")
            
            # 這裡可以初始化一些基本詞彙
            from services.vocabulary_service import DEFAULT_VOCABULARY
            for word, translation in DEFAULT_VOCABULARY:
                try:
                    cursor.execute(
                        "INSERT INTO vocabulary (english_word, chinese_translation) VALUES (?, ?)",
                        (word, translation)
                    )
                except sqlite3.IntegrityError:
                    # 忽略重複詞彙
                    pass
            
            print(f"✅ 已嘗試插入 {len(DEFAULT_VOCABULARY)} 個預設詞彙")
        
        if 'word_usage' not in existing_tables:
            print("創建 word_usage 表...")
            cursor.execute('''
                CREATE TABLE word_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    word_ids TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ 已創建 word_usage 表")
        
        conn.commit()
        print("✅ 數據庫結構檢查和更新完成")
        
        conn.close()
        print("數據庫連接已關閉")
        
    except Exception as e:
        print(f"❌ 更新數據庫時出錯: {e}")
        raise  # 重新拋出異常以便應用程序可以處理
