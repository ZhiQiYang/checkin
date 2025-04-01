import sqlite3
import os
from config import Config
from services.vocabulary_service import DEFAULT_VOCABULARY

def reset_vocabulary_database():
    """重置詞彙數據庫，刪除現有表並重新創建，使用新的詞彙集"""
    try:
        # 檢查數據庫文件是否存在
        if not os.path.exists(Config.DB_PATH):
            print(f"數據庫文件不存在: {Config.DB_PATH}")
            return False
        
        # 連接到數據庫
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # 刪除現有的詞彙相關表（如果存在）
        print("刪除現有的詞彙表...")
        cursor.execute("DROP TABLE IF EXISTS vocabulary")
        cursor.execute("DROP TABLE IF EXISTS word_usage")
        
        # 創建詞彙表
        print("創建新的詞彙表...")
        cursor.execute('''
            CREATE TABLE vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                english_word TEXT UNIQUE NOT NULL,
                chinese_translation TEXT NOT NULL,
                difficulty INTEGER DEFAULT 2,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 創建已使用詞彙記錄表
        print("創建詞彙使用記錄表...")
        cursor.execute('''
            CREATE TABLE word_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                word_ids TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 插入預設詞彙
        print("插入新的詞彙數據...")
        for word_data in DEFAULT_VOCABULARY:
            try:
                if len(word_data) == 3:
                    word, translation, difficulty = word_data
                    cursor.execute(
                        "INSERT INTO vocabulary (english_word, chinese_translation, difficulty) VALUES (?, ?, ?)",
                        (word, translation, difficulty)
                    )
                else:
                    word, translation = word_data
                    cursor.execute(
                        "INSERT INTO vocabulary (english_word, chinese_translation) VALUES (?, ?)",
                        (word, translation)
                    )
            except sqlite3.IntegrityError as e:
                print(f"跳過重複詞彙 '{word}': {e}")
        
        # 提交更改
        conn.commit()
        
        # 確認插入的詞彙數量
        cursor.execute("SELECT COUNT(*) FROM vocabulary")
        count = cursor.fetchone()[0]
        
        print(f"✅ 詞彙數據庫重置完成，已插入 {count} 個新詞彙")
        
        # 關閉連接
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 重置詞彙數據庫時出錯: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return False

if __name__ == "__main__":
    reset_vocabulary_database() 