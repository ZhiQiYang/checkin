# services/checkin_service.py
from datetime import datetime
from db.crud import save_checkin

# 更新 services/checkin_service.py 中的 process_checkin 函數
def process_checkin(user_id, name, location, note=None, latitude=None, longitude=None, checkin_type="上班"):
    """處理打卡，保存打卡記錄到數據庫"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        today = datetime.now().strftime("%Y-%m-%d")
        time_str = datetime.now().strftime("%H:%M:%S")
        
        # 簡化代碼：直接調用 save_checkin
        success, message = save_checkin(user_id, name, location, note, latitude, longitude, checkin_type)
        
        print(f"打卡結果: {success}, {message}, {timestamp}")
        
        return success, message, timestamp

    
    except Exception as e:
        print(f"打卡過程錯誤: {str(e)}")
        return False, f"處理過程出錯: {str(e)}", datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def quick_checkin(user_id, name, checkin_type="上班"):
    """快速打卡功能"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success, message = save_checkin(user_id, name, f"快速{checkin_type}打卡", 
                                    note=f"通過指令快速{checkin_type}打卡", 
                                    checkin_type=checkin_type)
    return success, message, timestamp

# 向後兼容的別名
save_checkin_record = process_checkin
