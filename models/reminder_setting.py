"""
提醒設置模型，對應數據庫中的reminder_settings表
"""

from datetime import datetime
from models.base import Model, Database

class ReminderSetting(Model):
    """提醒設置模型類，用於管理用戶的簽到提醒設定"""
    
    table_name = "reminder_settings"
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "TEXT UNIQUE NOT NULL",
        "checkin_reminder": "BOOLEAN DEFAULT 1",
        "checkin_time": "TEXT DEFAULT '09:00'",
        "checkout_reminder": "BOOLEAN DEFAULT 1",
        "checkout_time": "TEXT DEFAULT '18:00'",
        "weekly_report": "BOOLEAN DEFAULT 1",
        "monthly_report": "BOOLEAN DEFAULT 1",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }
    
    @classmethod
    def get_by_user_id(cls, user_id):
        """通過用戶ID獲取提醒設置"""
        query = f"SELECT * FROM {cls.table_name} WHERE user_id = ?"
        result = Database.execute_query(query, (user_id,), 'one')
        
        if not result:
            # 創建默認設置
            return cls.create_default_settings(user_id)
            
        return cls._row_to_dict(result)
    
    @classmethod
    def create_default_settings(cls, user_id):
        """為新用戶創建默認提醒設置"""
        data = {
            'user_id': user_id,
            'checkin_reminder': True,
            'checkin_time': '09:00',
            'checkout_reminder': True,
            'checkout_time': '18:00',
            'weekly_report': True,
            'monthly_report': True
        }
        
        setting_id = cls.insert(data)
        return cls.find_by_id(setting_id)
    
    @classmethod
    def update_settings(cls, user_id, settings):
        """更新用戶提醒設置"""
        existing = cls.get_by_user_id(user_id)
        
        # 如果未找到設置，創建默認設置
        if not existing:
            return cls.create_default_settings(user_id)
            
        # 更新設置
        settings['updated_at'] = 'CURRENT_TIMESTAMP'
        updated = cls.update(existing['id'], settings)
        return cls.find_by_id(existing['id'])
    
    @classmethod
    def get_users_for_reminder(cls, reminder_type, reminder_time=None):
        """根據提醒類型和時間獲取需要提醒的用戶列表
        
        reminder_type: checkin_reminder, checkout_reminder
        reminder_time: 時間字符串，如 '09:00'
        """
        time_field = f"{reminder_type.split('_')[0]}_time"
        
        conditions = [f"{reminder_type} = 1"]
        params = []
        
        if reminder_time:
            conditions.append(f"{time_field} = ?")
            params.append(reminder_time)
            
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT rs.user_id, u.name, u.line_user_id, rs.{time_field} as reminder_time
            FROM {cls.table_name} rs
            JOIN users u ON rs.user_id = u.id
            WHERE {where_clause} AND u.is_active = 1
        """
        
        results = Database.execute_query(query, tuple(params), 'all')
        return [dict(zip(['user_id', 'name', 'line_user_id', 'reminder_time'], row)) for row in results] if results else []
    
    @classmethod
    def get_users_for_report(cls, report_type):
        """獲取需要接收報告的用戶列表
        
        report_type: weekly_report, monthly_report
        """
        query = f"""
            SELECT rs.user_id, u.name, u.line_user_id
            FROM {cls.table_name} rs
            JOIN users u ON rs.user_id = u.id
            WHERE rs.{report_type} = 1 AND u.is_active = 1
        """
        
        results = Database.execute_query(query, None, 'all')
        return [dict(zip(['user_id', 'name', 'line_user_id'], row)) for row in results] if results else []
    
    @staticmethod
    def log_reminder(user_id, reminder_type):
        """記錄已發送的提醒"""
        # 確認reminder_logs表存在
        query = """
            CREATE TABLE IF NOT EXISTS reminder_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                sent_at DATETIME,
                status TEXT
            )
        """
        Database.execute_query(query)
        
        # 記錄提醒
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        insert_query = "INSERT INTO reminder_logs (user_id, reminder_type, sent_at, status) VALUES (?, ?, ?, ?)"
        try:
            Database.execute_query(insert_query, (user_id, reminder_type, now, 'sent'))
            return True
        except Exception as e:
            print(f"記錄提醒日誌時出錯: {e}")
            return False
    
    @staticmethod
    def _row_to_dict(row):
        """將數據庫結果轉換為字典"""
        if not row:
            return None
            
        columns = [
            'id', 'user_id', 'checkin_reminder', 'checkin_time',
            'checkout_reminder', 'checkout_time', 'weekly_report',
            'monthly_report', 'created_at', 'updated_at'
        ]
        
        result = {columns[i]: row[i] for i in range(len(columns)) if i < len(row)}
        
        # 將布爾值從整數轉換為布爾
        bool_fields = ['checkin_reminder', 'checkout_reminder', 'weekly_report', 'monthly_report']
        for field in bool_fields:
            if field in result:
                result[field] = bool(result[field])
                
        return result 