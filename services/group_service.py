import json
from utils.file_helper import ensure_file_exists
from config import GROUP_MESSAGES_FILE
from db.storage import ensure_file_exists, load_json, save_json
from config import Config

def get_recent_messages(count=20):
    """取得最近群組訊息"""
    data = load_json(Config.GROUP_MESSAGES_FILE, {"messages": []})
    return data["messages"][-count:]

def save_group_message(user_id, user_name, message, timestamp):
    """儲存群組訊息"""
    data = load_json(Config.GROUP_MESSAGES_FILE, {"messages": []})
    
    new_message = {
        "user_id": user_id,
        "user_name": user_name,
        "message": message,
        "timestamp": timestamp
    }
    data["messages"].append(new_message)
    
    # 只保留最近 100 筆
    data["messages"] = data["messages"][-100:]
    
    save_json(Config.GROUP_MESSAGES_FILE, data)
    with open(GROUP_MESSAGES_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 取得最近群組訊息
def get_recent_messages(count=20):
    ensure_group_messages_file()
    with open(GROUP_MESSAGES_FILE, 'r') as f:
        data = json.load(f)
    return data["messages"][-count:]
