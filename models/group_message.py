# models/group_message.py
from .base import Model, Database
from datetime import datetime

class GroupMessage(Model):
    table_name = "group_messages"
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "TEXT NOT NULL",
        "user_name": "TEXT NOT NULL",
        "message": "TEXT",
        "timestamp": "TEXT NOT NULL"
    }

    @classmethod
    def save_message(cls, user_id, user_name, message, timestamp):
        data = {
            'user_id': user_id,
            'user_name': user_name,
            'message': message,
            'timestamp': timestamp
        }
        return cls.insert(data)

    @classmethod
    def get_recent(cls, count=20):
        results = cls.find_all(order_by="id DESC", limit=count)
        # 需要將結果從元組轉換為字典
        return [cls._row_to_dict(row) for row in results] if results else []

    @staticmethod
    def _row_to_dict(row):
        if not row: return None
        cols = ['id', 'user_id', 'user_name', 'message', 'timestamp']
        return {cols[i]: row[i] for i in range(len(cols))} 