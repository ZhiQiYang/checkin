from db.storage import load_json, save_json
from config import Config

def get_recent_messages(count=20):
    """取得最近群組訊息"""
    data = load_json(Config.GROUP_MESSAGES_FILE, {"messages": []})
    return data["messages"][-count:]

def save_group_message(user_id, user_name, message, timestamp):
    conn = sqlite3.connect(Config.DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO group_messages (user_id, user_name, message, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (user_id, user_name, message, timestamp))
    conn.commit()
    conn.close()
