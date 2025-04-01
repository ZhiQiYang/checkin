import sqlite3
import os

def main():
    try:
        # 嘗試兩個可能的數據庫位置
        db_paths = ['checkin.db', os.path.join('db', 'checkin.db')]
        
        db_path = None
        for path in db_paths:
            if os.path.exists(path):
                db_path = path
                print(f"找到數據庫文件: {path}")
                break
                
        if not db_path:
            print("數據庫文件不存在")
            return

        # 連接到數據庫
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 檢查vocabulary表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vocabulary'")
        if not cursor.fetchone():
            print("vocabulary表不存在")
            return
        
        # 獲取詞彙總數
        cursor.execute("SELECT COUNT(*) FROM vocabulary")
        total_count = cursor.fetchone()[0]
        print(f"詞彙總數: {total_count}")
        
        # 獲取各難度級別的詞彙數量
        cursor.execute("SELECT difficulty, COUNT(*) FROM vocabulary GROUP BY difficulty")
        difficulty_stats = cursor.fetchall()
        for difficulty, count in difficulty_stats:
            print(f"難度 {difficulty}: {count} 個詞彙")
        
        # 檢查user_vocabulary表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_vocabulary'")
        has_user_vocab = cursor.fetchone() is not None
        print(f"user_vocabulary表存在: {has_user_vocab}")
        
        if has_user_vocab:
            # 檢查user_vocabulary表中的記錄數
            cursor.execute("SELECT COUNT(*) FROM user_vocabulary")
            user_vocab_count = cursor.fetchone()[0]
            print(f"user_vocabulary表中的記錄數: {user_vocab_count}")
            
            # 檢查不同用戶的記錄數
            cursor.execute("SELECT user_id, COUNT(*) FROM user_vocabulary GROUP BY user_id")
            user_stats = cursor.fetchall()
            for user_id, count in user_stats:
                print(f"用戶 {user_id} 已分配詞彙數: {count}")
    
    except Exception as e:
        print(f"檢查詞彙數據庫時出錯: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    main() 