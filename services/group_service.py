# services/group_service.py
from db.crud import save_group_message as db_save_message
from db.crud import get_recent_messages as db_get_messages

def get_recent_messages(count=20):
    """取得最近群組訊息"""
    return db_get_messages(count)

def save_group_message(user_id, user_name, message, timestamp):
    """儲存群組訊息"""
    db_save_message(user_id, user_name, message, timestamp)
