# services/group_service.py
from models import GroupMessage

def get_recent_messages(count=20):
    """取得最近群組訊息"""
    return GroupMessage.get_recent(count)

def save_group_message(user_id, user_name, message, timestamp):
    """儲存群組訊息"""
    GroupMessage.save_message(user_id, user_name, message, timestamp)
