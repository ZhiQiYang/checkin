"""
打卡記錄模型，對應數據庫中的checkin_records表
"""

from datetime import datetime
from models.base import Model, Database

class CheckinRecord(Model):
    """打卡記錄模型類"""
    
    table_name = "checkin_records"
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "TEXT NOT NULL",
        "name": "TEXT NOT NULL",
        "date": "TEXT NOT NULL",
        "time": "TEXT NOT NULL",
        "checkin_type": "TEXT NOT NULL",
        "location": "TEXT",
        "latitude": "REAL",
        "longitude": "REAL",
        "ip": "TEXT",
        "device": "TEXT",
        "note": "TEXT",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "updated_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }
    
    @classmethod
    def has_checkin_today(cls, user_id, checkin_type, date):
        """檢查用戶當天是否已有特定類型的打卡記錄"""
        query = f"SELECT 1 FROM {cls.table_name} WHERE user_id = ? AND date = ? AND checkin_type = ? LIMIT 1"
        result = Database.execute_query(query, (user_id, date, checkin_type), 'one')
        return result is not None
    
    @classmethod
    def get_user_records(cls, user_id, start_date=None, end_date=None, limit=30):
        """獲取用戶的打卡記錄"""
        conditions = "user_id = ?"
        params = [user_id]
        
        if start_date:
            conditions += " AND date >= ?"
            params.append(start_date)
            
        if end_date:
            conditions += " AND date <= ?"
            params.append(end_date)
            
        results = cls.find_all(conditions, tuple(params), "date DESC, time ASC", limit)
        return [cls._row_to_dict(row) for row in results] if results else []
    
    @classmethod
    def get_today_records(cls, date=None):
        """獲取今天的所有打卡記錄"""
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
            
        results = cls.find_all("date = ?", (date,), "time ASC")
        return [cls._row_to_dict(row) for row in results] if results else []
    
    @classmethod
    def get_user_record_by_date_type(cls, user_id, date, checkin_type):
        """獲取用戶特定日期和類型的打卡記錄"""
        query = f"SELECT * FROM {cls.table_name} WHERE user_id = ? AND date = ? AND checkin_type = ?"
        result = Database.execute_query(query, (user_id, date, checkin_type), 'one')
        return cls._row_to_dict(result) if result else None
    
    @classmethod
    def create_or_update(cls, data):
        """創建或更新打卡記錄"""
        required_fields = ['user_id', 'name', 'date', 'time', 'checkin_type']
        for field in required_fields:
            if field not in data:
                raise ValueError(f"缺少必要字段: {field}")
        
        # 檢查是否已有同類型的打卡記錄
        existing_record = cls.get_user_record_by_date_type(
            data['user_id'], data['date'], data['checkin_type']
        )
        
        if existing_record:
            # 更新現有記錄
            update_data = {k: v for k, v in data.items() if k != 'user_id' and k != 'date' and k != 'checkin_type'}
            update_data['updated_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cls.update(existing_record['id'], update_data)
            return cls.get_user_record_by_date_type(data['user_id'], data['date'], data['checkin_type'])
        else:
            # 創建新記錄
            record_id = cls.insert(data)
            return cls.find_by_id(record_id)
    
    @classmethod
    def get_statistics(cls, user_id, month=None):
        """獲取用戶打卡統計數據"""
        if not month:
            month = datetime.now().strftime("%Y-%m")
            
        start_date = f"{month}-01"
        
        # 計算下個月的第一天
        year, month_num = map(int, month.split('-'))
        if month_num == 12:
            next_year = year + 1
            next_month = 1
        else:
            next_year = year
            next_month = month_num + 1
            
        end_date = f"{next_year}-{next_month:02d}-01"
        
        # 獲取該月的所有打卡記錄
        query = f"""
            SELECT date, checkin_type, time
            FROM {cls.table_name}
            WHERE user_id = ? AND date >= ? AND date < ?
            ORDER BY date, time
        """
        
        results = Database.execute_query(query, (user_id, start_date, end_date), 'all')
        
        # 處理統計數據
        daily_records = {}
        for record in results:
            date, checkin_type, time = record
            if date not in daily_records:
                daily_records[date] = {"上班": None, "下班": None}
            daily_records[date][checkin_type] = time
        
        # 計算統計指標
        total_days = len(daily_records)
        on_time_days = 0
        late_days = 0
        no_checkin_days = 0
        overtime_days = 0
        
        for date, times in daily_records.items():
            if times["上班"] and times["下班"]:
                # 有上下班記錄，計算是否遲到和加班
                if times["上班"] <= "09:00:00":
                    on_time_days += 1
                else:
                    late_days += 1
                
                # 假設18:00為下班時間
                if times["下班"] >= "18:00:00":
                    overtime_days += 1
            elif not times["上班"] or not times["下班"]:
                no_checkin_days += 1
        
        return {
            "total_days": total_days,
            "on_time_days": on_time_days,
            "late_days": late_days,
            "no_checkin_days": no_checkin_days,
            "overtime_days": overtime_days,
            "daily_records": daily_records
        }
    
    @staticmethod
    def _row_to_dict(row):
        """將數據庫結果轉換為字典"""
        if not row:
            return None
        
        columns = [
            'id', 'user_id', 'name', 'date', 'time', 'checkin_type', 
            'location', 'latitude', 'longitude', 'ip', 'device', 
            'note', 'created_at', 'updated_at'
        ]
        
        return {columns[i]: row[i] for i in range(len(columns)) if i < len(row)} 