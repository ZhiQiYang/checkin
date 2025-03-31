# services/checkin_service.py
from datetime import datetime
from utils.timezone import get_current_time, get_date_string, get_time_string, get_datetime_string
from utils.timezone import get_current_time, get_date_string, get_time_string, get_datetime_string

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

def quick_checkin(user_id, name, checkin_type="上班"):
    """
    快速打卡功能，使用預設位置信息
    
    Args:
        user_id: 用戶ID
        name: 用戶名稱
        checkin_type: 打卡類型，預設為"上班"
        
    Returns:
        tuple: (success, message, timestamp) 同 process_checkin
    """
    location = f"快速{checkin_type}打卡"
    note = f"通過指令快速{checkin_type}打卡"
    
    return process_checkin(
        user_id=user_id,
        name=name,
        location=location,
        note=note,
        checkin_type=checkin_type
    )

# 向後兼容的別名，但標記為棄用
save_checkin_record = process_checkin
