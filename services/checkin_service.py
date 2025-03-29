from datetime import datetime
from utils.file_helper import load_json, save_json

def process_checkin(user_id, name, location, note=None, latitude=None, longitude=None):
    data = load_json('checkin_records.json')
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 已打卡檢查
    for r in data['records']:
        if r['user_id'] == user_id and r['date'] == today:
            return False, "今天已經打卡過了", timestamp

    # 新記錄
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
    save_json('checkin_records.json', data)
    return True, "打卡成功", timestamp

def quick_checkin(user_id, name):
    """
    快速打卡功能，不包含位置和備註
    """
    data = load_json('checkin_records.json')
    today = datetime.now().strftime("%Y-%m-%d")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 已打卡檢查
    for r in data['records']:
        if r['user_id'] == user_id and r['date'] == today:
            return False, "今天已經打卡過了"

    # 新記錄
    record = {
        "user_id": user_id,
        "name": name,
        "date": today,
        "time": timestamp,
        "location": "快速打卡",
        "note": "通過指令快速打卡"
    }

    data["records"].append(record)
    save_json('checkin_records.json', data)
    return True, "打卡成功"


# 在 services/checkin_service.py 文件末尾添加
save_checkin_record = process_checkin  # 添加別名，向後兼容
