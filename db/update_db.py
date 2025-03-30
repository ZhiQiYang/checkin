import sqlite3
from config import Config

def update_database():
    """更新數據庫結構，添加 checkin_type 列"""
    print("開始更新數據庫結構...")
    
    try:
        # 連接數據庫
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # 執行 ALTER TABLE 語句
        cursor.execute("ALTER TABLE checkin_records ADD COLUMN checkin_type TEXT DEFAULT '上班'")
        
        # 提交變更
        conn.commit()
        print("✅ 數據庫更新成功！添加了 checkin_type 列，默認值為 '上班'")
        
        # 驗證更改
        cursor.execute("PRAGMA table_info(checkin_records)")
        columns = cursor.fetchall()
        print("\n當前表結構:")
        for column in columns:
            print(f"- {column[1]} ({column[2]})")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("⚠️ checkin_type 列已存在，無需更改")
        else:
            print(f"❌ 錯誤: {e}")
    except Exception as e:
        print(f"❌ 發生未知錯誤: {e}")
    finally:
        # 關閉連接
        if 'conn' in locals():
            conn.close()
            print("\n數據庫連接已關閉")

if __name__ == "__main__":
    update_database()
