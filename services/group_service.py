from db.storage import load_json, save_json
from config import Config

def get_recent_messages(count=20):
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute('''
        SELECT * FROM group_messages 
        ORDER BY id DESC LIMIT ?
    ''', (count,))
    results = c.fetchall()
    conn.close()
    
    # 轉換為字典列表
    messages = []
    for row in results:
        messages.append({
            "user_id": row["user_id"],
            "user_name": row["user_name"],
            "message": row["message"],
            "timestamp": row["timestamp"]
        })
    return messages

def save_group_message(user_id, user_name, message, timestamp):
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO group_messages (user_id, user_name, message, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, user_name, message, timestamp))
    conn.commit()
    conn.close()
