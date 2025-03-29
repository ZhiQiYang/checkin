import json
from utils.file_helper import ensure_file_exists
from config import GROUP_MESSAGES_FILE

# 確保群組訊息檔案存在
def ensure_group_messages_file():
    ensure_file_exists(GROUP_MESSAGES_FILE, {"messages": []})

# 儲存群組訊息
def save_group_message(user_id, user_name, message, timestamp):
    ensure_group_messages_file()

    with open(GROUP_MESSAGES_FILE, 'r') as f:
        data = json.load(f)

    new_message = {
        "user_id": user_id,
        "user_name": user_name,
        "message": message,
        "timestamp": timestamp
    }
    data["messages"].append(new_message)

    # 只保留最近 100 筆
    data["messages"] = data["messages"][-100:]

    with open(GROUP_MESSAGES_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 取得最近群組訊息
def get_recent_messages(count=20):
    ensure_group_messages_file()
    with open(GROUP_MESSAGES_FILE, 'r') as f:
        data = json.load(f)
    return data["messages"][-count:]
