# db/update_db.py
import sqlite3
import os
from config import Config

def update_database():
    """檢查並更新數據庫結構，保留現有數據"""
    print("檢查數據庫結構...")
    
    db_path = Config.DB_PATH # 使用 Config 中的路徑
    db_dir = os.path.dirname(db_path)

    # 確保數據庫目錄存在
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            print(f"創建數據庫目錄: {db_dir}")
        except Exception as e:
            print(f"無法創建數據庫目錄 {db_dir}: {e}")

    # 檢查數據庫文件是否存在，如果不存在則創建空文件
    if not os.path.exists(db_path):
        print(f"數據庫文件 {db_path} 不存在，創建空數據庫...")
        try:
            conn = sqlite3.connect(db_path)
            conn.close()
            print(f"✅ 創建了新的空數據庫文件: {db_path}")
        except Exception as e:
            print(f"❌ 創建空數據庫文件 {db_path}
            失敗: {e}")
        # 不再 return，讓後續的 Model 檢查來創建表
    
    try:
        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 獲取現有表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in cursor.fetchall()]
        print(f"現有表: {existing_tables}")
        
        # --- 只保留結構修改 (ALTER TABLE) 的邏輯 ---
        # 檢查並更新 checkin_records 表
        if 'checkin_records' in existing_tables:
            print("檢查 checkin_records 表結構...")
            cursor.execute("PRAGMA table_info(checkin_records)")
            columns = [col[1] for col in cursor.fetchall()]
            
            # 如果缺少 checkin_type 列，添加它
            if 'checkin_type' not in columns:
                print("添加 checkin_type 列到 checkin_records 表...")
                try:
                    cursor.execute("ALTER TABLE checkin_records ADD COLUMN checkin_type TEXT DEFAULT '上班'")
                    print("✅ 已添加 checkin_type 列")
                except sqlite3.OperationalError as alter_err:
                    # 如果並發執行，可能另一進程已添加
                    if "duplicate column name" in str(alter_err):
                        print("⚠️ checkin_type 列已存在")
                    else:
                        print(f"❌ 添加 checkin_type 列失敗: {alter_err}")
                        raise alter_err # 拋出以便上層知道
            
            # 添加 created_at 和 updated_at (如果不存在)
            if 'created_at' not in columns:
                 print("添加 created_at 列到 checkin_records 表...")
                 cursor.execute("ALTER TABLE checkin_records ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                 print("✅ 已添加 created_at 列")
            if 'updated_at' not in columns:
                 print("添加 updated_at 列到 checkin_records 表...")
                 cursor.execute("ALTER TABLE checkin_records ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP")
                 print("✅ 已添加 updated_at 列")
        
        # --- 移除所有 CREATE TABLE 語句 ---
        # if 'users' not in existing_tables: ... (刪除)
        # if 'reminder_settings' not in existing_tables: ... (刪除)
        # if 'reminder_logs' not in existing_tables: ... (刪除)
        # if 'vocabulary' not in existing_tables: ... (刪除)
        # if 'word_usage' not in existing_tables: ... (刪除)
        # ---
        
        conn.commit()
        print("✅ 數據庫結構*更新*檢查完成")
        
        conn.close()
        print("數據庫連接已關閉 (來自 update_db)")
        
    except Exception as e:
        print(f"❌ 更新數據庫結構時出錯: {e}")
        import traceback
        print(traceback.format_exc())
        # 考慮是否需要拋出異常，讓 app 啟動失敗
        # raise e
