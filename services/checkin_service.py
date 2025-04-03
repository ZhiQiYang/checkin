# services/checkin_service.py
from datetime import datetime, timedelta
from utils.timezone import get_current_time, get_date_string, get_time_string, get_datetime_string
from utils.timezone import get_current_time, get_date_string, get_time_string, get_datetime_string
from models import CheckinRecord, User

from db.crud import (
    insert_checkin_record, 
    has_checkin_today, 
    save_or_update_user
)

def process_checkin(user_id, name, location, note=None, latitude=None, longitude=None, checkin_type="上班"):
    """
    處理打卡請求的核心邏輯，包含所有業務規則檢查
    
    Args:
        user_id: 用戶ID
        name: 用戶名稱
        location: 打卡位置
        note: 備註信息
        latitude: 緯度
        longitude: 經度
        checkin_type: 打卡類型，預設為"上班"
        
    Returns:
        tuple: (success, message, timestamp)
            - success: 布爾值，表示打卡是否成功
            - message: 打卡結果消息
            - timestamp: 打卡時間戳
    """
    try:
        # 保存用戶信息
        save_or_update_user(user_id, name)

        from utils.timezone import get_current_time, get_date_string, get_time_string, get_datetime_string
        # 取得當前日期和時間
        today = get_date_string()
        time_str = get_time_string()
        timestamp = get_datetime_string()
        
        # 檢查是否已有相同類型的打卡記錄
        if has_checkin_today(user_id, checkin_type, today):
            return False, f"今天已經{checkin_type}打卡過了", timestamp
        
        # 如果是下班打卡，檢查今天是否已經有上班打卡
        if checkin_type == "下班" and not has_checkin_today(user_id, "上班", today):
            return False, "請先完成上班打卡，才能進行下班打卡", timestamp
            
        # 插入打卡記錄
        success = insert_checkin_record(
            user_id, name, location, note, 
            latitude, longitude, today, time_str, checkin_type
        )
        
        if success:
            print(f"打卡成功: 用戶={name}, 類型={checkin_type}, 時間={timestamp}")
            return True, f"{checkin_type}打卡成功", timestamp
        else:
            return False, "數據庫操作失敗，請稍後再試", timestamp
            
    except Exception as e:
        print(f"打卡過程錯誤: {str(e)}")
        return False, f"處理過程出錯: {str(e)}", utils.timezone.get_current_time().strftime("%Y-%m-%d %H:%M:%S")

def quick_checkin(user_id, name, checkin_type="上班", location=None, note=None, latitude=None, longitude=None):
    """
    快速打卡功能，使用預設位置信息
    
    Args:
        user_id: 用戶ID
        name: 用戶名稱
        checkin_type: 打卡類型，預設為"上班"
        location: 可選，位置名稱
        note: 可選，備註信息
        latitude: 可選，緯度
        longitude: 可選，經度
        
    Returns:
        tuple: (success, message, timestamp) 同 process_checkin
    """
    # 如果沒有提供位置信息，使用預設值
    if location is None:
        location = f"快速{checkin_type}打卡"
    
    # 如果沒有提供備註，使用預設值
    if note is None:
        note = f"通過指令快速{checkin_type}打卡"
    
    return process_checkin(
        user_id=user_id,
        name=name,
        location=location,
        note=note,
        latitude=latitude,
        longitude=longitude,
        checkin_type=checkin_type
    )

# 向後兼容的別名，但標記為棄用
save_checkin_record = process_checkin

def record_checkin(user_id, checkin_data):
    """
    記錄用戶簽到
    
    Args:
        user_id: 用戶ID
        checkin_data: 簽到數據，包含name, checkin_type, location等字段
        
    Returns:
        記錄ID或None（失敗時）
    """
    try:
        # 確保數據表存在
        CheckinRecord.create_table_if_not_exists()
        
        # 獲取當前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        current_time = datetime.now().strftime('%H:%M:%S')
        
        # 合併數據
        data = {
            'user_id': user_id,
            'date': current_date,
            'time': current_time,
            **checkin_data
        }
        
        # 創建或更新記錄
        result = CheckinRecord.create_or_update(data)
        return result
    
    except Exception as e:
        print(f"記錄簽到時出錯: {str(e)}")
        return None


def get_user_records(user_id, start_date=None, end_date=None, limit=30):
    """
    獲取用戶的簽到記錄
    
    Args:
        user_id: 用戶ID
        start_date: 開始日期（可選）
        end_date: 結束日期（可選）
        limit: 記錄數量限制
        
    Returns:
        簽到記錄列表
    """
    try:
        # 確保數據表存在
        CheckinRecord.create_table_if_not_exists()
        
        # 獲取記錄
        records = CheckinRecord.get_user_records(user_id, start_date, end_date, limit)
        return records
    
    except Exception as e:
        print(f"獲取用戶簽到記錄時出錯: {str(e)}")
        return []


def get_today_records(date=None):
    """
    獲取今日所有簽到記錄
    
    Args:
        date: 日期，默認為今天
        
    Returns:
        簽到記錄列表
    """
    try:
        # 確保數據表存在
        CheckinRecord.create_table_if_not_exists()
        
        # 如果未提供日期，使用今天
        if not date:
            date = datetime.now().strftime('%Y-%m-%d')
            
        # 獲取記錄
        records = CheckinRecord.get_today_records(date)
        return records
    
    except Exception as e:
        print(f"獲取今日簽到記錄時出錯: {str(e)}")
        return []


def get_checkin_statistics(user_id, month=None):
    """
    獲取用戶簽到統計信息
    
    Args:
        user_id: 用戶ID
        month: 月份（YYYY-MM格式，可選）
        
    Returns:
        統計信息字典
    """
    try:
        # 確保數據表存在
        CheckinRecord.create_table_if_not_exists()
        
        # 獲取統計信息
        stats = CheckinRecord.get_statistics(user_id, month)
        return stats
    
    except Exception as e:
        print(f"獲取簽到統計信息時出錯: {str(e)}")
        return {
            'total_days': 0,
            'on_time_days': 0,
            'late_days': 0,
            'no_checkin_days': 0,
            'overtime_days': 0
        }
