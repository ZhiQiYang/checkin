"""
用戶模型，對應數據庫中的users表
"""

from datetime import datetime
from models.base import Model, Database

class User(Model):
    """用戶模型類"""
    
    table_name = "users"
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "line_user_id": "TEXT UNIQUE NOT NULL",
        "name": "TEXT NOT NULL",
        "email": "TEXT",
        "department": "TEXT",
        "position": "TEXT",
        "phone": "TEXT",
        "profile_image_url": "TEXT",
        "is_active": "INTEGER DEFAULT 1",
        "is_admin": "INTEGER DEFAULT 0",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }
    
    @classmethod
    def find_by_line_id(cls, line_user_id):
        """通過LINE用戶ID查找用戶"""
        query = f"SELECT * FROM {cls.table_name} WHERE line_user_id = ?"
        result = Database.execute_query(query, (line_user_id,), 'one')
        return cls._row_to_dict(result) if result else None
    
    @classmethod
    def create_or_update(cls, line_user_id, data):
        """創建或更新用戶"""
        # 檢查用戶是否存在
        existing_user = cls.find_by_line_id(line_user_id)
        
        if existing_user:
            # 更新現有用戶
            data['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cls.update(existing_user['id'], data)
            return cls.find_by_line_id(line_user_id)
        else:
            # 創建新用戶
            data['line_user_id'] = line_user_id
            user_id = cls.insert(data)
            return cls.find_by_id(user_id)
    
    @classmethod
    def get_active_users(cls):
        """獲取所有活躍用戶"""
        return cls.find_all("is_active = 1", order_by="name")
    
    @classmethod
    def get_admin_users(cls):
        """獲取所有管理員用戶"""
        return cls.find_all("is_admin = 1", order_by="name")
    
    @staticmethod
    def _row_to_dict(row):
        """將數據庫結果轉換為字典"""
        if not row:
            return None
        
        columns = [
            'id', 'line_user_id', 'name', 'email', 'department', 
            'position', 'phone', 'profile_image_url', 'is_active', 
            'is_admin', 'created_at', 'updated_at'
        ]
        
        return {columns[i]: row[i] for i in range(len(columns)) if i < len(row)} 