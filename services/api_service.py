import logging
import sqlite3
from datetime import datetime, timedelta
from config import Config
from services.user_service import UserService
import json

logger = logging.getLogger(__name__)

class ApiService:
    """處理REST API請求的服務類"""
    
    @staticmethod
    def create_checkin_record(data):
        """創建打卡記錄"""
        try:
            # 必要參數檢查
            required_fields = ['userId', 'name', 'type', 'date', 'time']
            for field in required_fields:
                if field not in data:
                    return {"success": False, "error": f"缺少必要參數: {field}"}
            
            user_id = data['userId']
            name = data['name']
            checkin_type = data['type']
            date = data['date']
            time = data['time']
            location = data.get('location', '')
            ip = data.get('ip', '')
            device = data.get('device', '')
            
            # 數據驗證
            if checkin_type not in ['上班', '下班']:
                return {"success": False, "error": "打卡類型必須是上班或下班"}
            
            # 連接數據庫
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()
            
            # 檢查是否已有同類型的打卡記錄
            cursor.execute(
                "SELECT id FROM checkin_records WHERE user_id = ? AND date = ? AND checkin_type = ?",
                (user_id, date, checkin_type)
            )
            existing_record = cursor.fetchone()
            
            if existing_record:
                # 更新現有記錄
                cursor.execute(
                    """
                    UPDATE checkin_records 
                    SET time = ?, location = ?, ip = ?, device = ?, updated_at = datetime('now')
                    WHERE user_id = ? AND date = ? AND checkin_type = ?
                    """,
                    (time, location, ip, device, user_id, date, checkin_type)
                )
                record_id = existing_record[0]
                message = "打卡記錄已更新"
            else:
                # 創建新記錄
                cursor.execute(
                    """
                    INSERT INTO checkin_records (user_id, name, date, time, checkin_type, location, ip, device)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (user_id, name, date, time, checkin_type, location, ip, device)
                )
                record_id = cursor.lastrowid
                message = "打卡成功"
            
            conn.commit()
            conn.close()
            
            return {
                "success": True,
                "message": message,
                "recordId": record_id,
                "data": {
                    "userId": user_id,
                    "name": name,
                    "date": date,
                    "time": time,
                    "type": checkin_type,
                    "location": location
                }
            }
        
        except Exception as e:
            logger.error(f"創建打卡記錄時出錯: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_records(user_id, start_date=None, end_date=None, limit=30):
        """獲取用戶打卡記錄"""
        try:
            if not user_id:
                return {"success": False, "error": "缺少用戶ID"}
            
            # 預設日期範圍為最近30天
            if not end_date:
                end_date = datetime.now().strftime("%Y-%m-%d")
            if not start_date:
                # 計算30天前的日期
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                start_dt = end_dt - timedelta(days=30)
                start_date = start_dt.strftime("%Y-%m-%d")
            
            # 連接數據庫
            conn = sqlite3.connect(Config.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查詢用戶打卡記錄
            cursor.execute(
                """
                SELECT * FROM checkin_records 
                WHERE user_id = ? AND date BETWEEN ? AND ? 
                ORDER BY date DESC, time ASC
                LIMIT ?
                """,
                (user_id, start_date, end_date, limit)
            )
            
            records = cursor.fetchall()
            conn.close()
            
            # 格式化記錄
            formatted_records = []
            for record in records:
                record_dict = dict(record)
                formatted_records.append({
                    "id": record_dict["id"],
                    "userId": record_dict["user_id"],
                    "name": record_dict["name"],
                    "date": record_dict["date"],
                    "time": record_dict["time"],
                    "type": record_dict["checkin_type"],
                    "location": record_dict["location"],
                    "createdAt": record_dict["created_at"]
                })
            
            return {
                "success": True,
                "data": formatted_records,
                "total": len(formatted_records),
                "startDate": start_date,
                "endDate": end_date
            }
            
        except Exception as e:
            logger.error(f"獲取用戶打卡記錄時出錯: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def get_user_statistics(user_id, month=None):
        """獲取用戶打卡統計數據"""
        try:
            if not user_id:
                return {"success": False, "error": "缺少用戶ID"}
            
            # 設置月份範圍
            if not month:
                month = datetime.now().strftime("%Y-%m")
            
            start_date = f"{month}-01"
            if month.endswith("12"):
                next_year = str(int(month.split('-')[0]) + 1)
                next_month = f"{next_year}-01"
            else:
                year = month.split('-')[0]
                month_num = int(month.split('-')[1])
                next_month = f"{year}-{month_num+1:02d}"
            
            end_date = f"{next_month}-01"
            
            # 連接數據庫
            conn = sqlite3.connect(Config.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 查詢該月的打卡記錄
            cursor.execute(
                """
                SELECT date, checkin_type, time
                FROM checkin_records 
                WHERE user_id = ? AND date >= ? AND date < ? 
                ORDER BY date, time
                """,
                (user_id, start_date, end_date)
            )
            
            records = cursor.fetchall()
            conn.close()
            
            # 處理統計數據
            daily_records = {}
            for record in records:
                date = record["date"]
                checkin_type = record["checkin_type"]
                time = record["time"]
                
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
            
            statistics = {
                "totalDays": total_days,
                "onTimeDays": on_time_days,
                "lateDays": late_days,
                "noCheckinDays": no_checkin_days,
                "overtimeDays": overtime_days,
                "dailyRecords": daily_records
            }
            
            return {
                "success": True,
                "data": statistics,
                "month": month
            }
            
        except Exception as e:
            logger.error(f"獲取用戶統計數據時出錯: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def create_or_update_user(data):
        """創建或更新用戶資料"""
        try:
            # 必要參數檢查
            if 'lineUserId' not in data:
                return {"success": False, "error": "缺少必要參數: lineUserId"}
            
            user_id = data['lineUserId']
            
            # 使用UserService獲取或創建用戶
            user = UserService.get_user_info(user_id)
            
            # 更新用戶資料
            settings = {}
            for key, value in data.items():
                if key == 'lineUserId':
                    continue
                
                # 將前端字段名轉換為數據庫字段名
                if key == 'name':
                    settings['name'] = value
                elif key == 'email':
                    settings['email'] = value
                elif key == 'department':
                    settings['department'] = value
                elif key == 'position':
                    settings['position'] = value
                elif key == 'phone':
                    settings['phone'] = value
            
            # 如果有需要更新的設置
            if settings:
                success = UserService.update_user_settings(user_id, settings)
                if not success:
                    return {"success": False, "error": "更新用戶設置失敗"}
            
            # 重新獲取最新用戶資料
            updated_user = UserService.get_user_info(user_id)
            
            if updated_user:
                return {
                    "success": True,
                    "message": "用戶資料已更新",
                    "data": {
                        "id": updated_user.get("id"),
                        "lineUserId": updated_user.get("line_user_id"),
                        "name": updated_user.get("name"),
                        "email": updated_user.get("email"),
                        "department": updated_user.get("department"),
                        "position": updated_user.get("position"),
                        "phone": updated_user.get("phone"),
                        "profileImage": updated_user.get("profile_image_url")
                    }
                }
            else:
                return {"success": False, "error": "獲取更新後的用戶資料失敗"}
            
        except Exception as e:
            logger.error(f"創建或更新用戶資料時出錯: {str(e)}")
            return {"success": False, "error": str(e)} 