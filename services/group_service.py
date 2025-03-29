from db.storage import load_json, save_json
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
