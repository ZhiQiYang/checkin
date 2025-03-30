# services/checkin_service.py
from datetime import datetime
from db.crud import save_checkin

def process_checkin(user_id, name, location, note=None, latitude=None, longitude=None):
    """處理打卡，保存打卡記錄到數據庫"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today = datetime.now().strftime("%Y-%m-%d")
    time_str = datetime.now().strftime("%H:%M:%S")
    
    # 使用資料庫函數保存打卡記錄
    success, message = save_checkin(user_id, name, location, note, latitude, longitude)
    
    return success, message, timestamp

def quick_checkin(user_id, name):
    """快速打卡功能"""
    return process_checkin(user_id, name, "快速打卡", note="通過指令快速打卡")

# 向後兼容的別名
save_checkin_record = process_checkin
