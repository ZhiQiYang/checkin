# services/checkin_service.py
from datetime import datetime
from db.crud import save_checkin
import sqlite3
from db.crud import DB_PATH

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

# 修改 services/checkin_service.py 中的 quick_checkin 函數

def quick_checkin(user_id, name, checkin_type="上班"):
    """快速打卡功能，包含順序檢查"""
    try:
        # 如果是下班打卡，檢查今天是否已經有上班打卡
        if checkin_type == "下班":
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            
            # 取得今天日期
            today = datetime.now().strftime('%Y-%m-%d')
            
            # 檢查今天是否已有上班打卡記錄
            c.execute('SELECT * FROM checkin_records WHERE user_id = ? AND date = ? AND checkin_type = ?', 
                    (user_id, today, "上班"))
            
            has_checked_in = c.fetchone() is not None
            conn.close()
            
            if not has_checked_in:
                return False, "請先完成上班打卡，才能進行下班打卡", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        print(f"檢查上班打卡記錄時出錯: {str(e)}")
        # 發生錯誤時繼續處理，讓主要的打卡邏輯有機會執行
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success, message = save_checkin(user_id, name, f"快速{checkin_type}打卡", 
                                    note=f"通過指令快速{checkin_type}打卡", 
                                    checkin_type=checkin_type)
    return success, message, timestamp
# 向後兼容的別名
save_checkin_record = process_checkin
