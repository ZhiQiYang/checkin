"""
用戶模型，對應數據庫中的users表
"""

from datetime import datetime
from models.base import Model, Database

class User(Model):
    """用戶模型類"""
    
    table_name = "users"
    columns = {
        # "id": "INTEGER PRIMARY KEY AUTOINCREMENT",  # 無需id列，主鍵是user_id
        "user_id": "TEXT PRIMARY KEY",                # 使用user_id作為主鍵，而不是line_user_id
        "name": "TEXT NOT NULL",
        "display_name": "TEXT",                       # 匹配實際表結構
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
        # 移除不存在的欄位
    }
    primary_key = "user_id"  # 覆蓋基類的primary_key設置
    
    @classmethod
    def find_by_line_id(cls, user_id):
        """通過LINE用戶ID查找用戶"""
        query = f"SELECT * FROM {cls.table_name} WHERE user_id = ?"
        result = Database.execute_query(query, (user_id,), 'one')
        return cls._row_to_dict(result) if result else None
    
    @classmethod
    def create_or_update(cls, user_id, data):
        """創建或更新用戶"""
        # 檢查用戶是否存在
        existing_user = cls.find_by_line_id(user_id)
        
        if existing_user:
            # 更新現有用戶的邏輯
            # 注意：這裡我們現在直接使用user_id作為主鍵
            for key, value in data.items():
                if key != 'user_id':  # 不更新主鍵
                    existing_user[key] = value
            
            # 執行更新操作
            update_fields = []
            update_values = []
            for key, value in data.items():
                if key != 'user_id':  # 不更新主鍵
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            if update_fields:
                query = f"UPDATE {cls.table_name} SET {', '.join(update_fields)} WHERE user_id = ?"
                update_values.append(user_id)
                Database.execute_query(query, tuple(update_values))
            
            return cls.find_by_line_id(user_id)
        else:
            # 創建新用戶
            data['user_id'] = user_id
            
            # 構建INSERT查詢
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {cls.table_name} ({columns}) VALUES ({placeholders})"
            
            # 執行INSERT
            Database.execute_query(query, tuple(data.values()))
            
            return cls.find_by_line_id(user_id)
    
    @classmethod
    def get_active_users(cls):
        """獲取所有用戶"""
        return cls.find_all(order_by="name")
    
    @classmethod
    def get_admin_users(cls):
        """獲取所有管理員用戶"""
        return cls.find_all("is_admin = 1", order_by="name")
    
    @staticmethod
    def _row_to_dict(row):
        """將數據庫結果轉換為字典"""
        if not row:
            return None
        
        # 更新列名以匹配實際表結構
        columns = ['user_id', 'name', 'display_name', 'created_at']
        
        return {columns[i]: row[i] for i in range(len(columns)) if i < len(row)} 