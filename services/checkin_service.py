# services/checkin_service.py
from datetime import datetime
from db.storage import load_json, save_json
from config import Config

def process_checkin(user_id, name, location, note=None, latitude=None, longitude=None):
    """處理打卡，保存打卡記錄"""
    data = load_json(Config.CHECKIN_FILE, {"records": []})
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 檢查是否已打卡
    for r in data['records']:
        if r['user_id'] == user_id and r['date'] == today:
            return False, "今天已經打卡過了", timestamp
    
    # 創建記錄
    record = {
        "user_id": user_id,
        "name": name,
        "date": today,
        "time": timestamp,
        "location": location,
        "note": note
    }
    
    if latitude and longitude:
        record["coordinates"] = {
            "latitude": float(latitude),
            "longitude": float(longitude)
        }
    
    data["records"].append(record)
    save_json(Config.CHECKIN_FILE, data)
    return True, "打卡成功", timestamp

def quick_checkin(user_id, name):
    """快速打卡功能"""
    return process_checkin(user_id, name, "快速打卡", note="通過指令快速打卡")

# 向後兼容的別名
save_checkin_record = process_checkin
