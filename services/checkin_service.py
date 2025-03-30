# services/checkin_service.py
from datetime import datetime
from db.crud import save_checkin

def process_checkin(user_id, name, location, note=None, latitude=None, longitude=None, checkin_type="上班"):
    """處理打卡，保存打卡記錄到數據庫"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    
    # 檢查今天是否已有相同類型的打卡記錄
    success, message = save_checkin(user_id, name, location, note, latitude, longitude, checkin_type)
    
    return success, message, timestamp

def quick_checkin(user_id, name, checkin_type="上班"):
    """快速打卡功能"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success, message = save_checkin(user_id, name, f"快速{checkin_type}打卡", 
                                    note=f"通過指令快速{checkin_type}打卡", 
                                    checkin_type=checkin_type)
    return success, message, timestamp

# 向後兼容的別名
save_checkin_record = process_checkin
