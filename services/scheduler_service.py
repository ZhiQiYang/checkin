# 修改 services/scheduler_service.py

import threading
import time
import schedule
from datetime import datetime
import pytz
from db.crud import get_users_needing_reminder, log_reminder
from services.notification_service import send_line_notification
from config import Config
from utils.timezone import get_current_time, get_timezone  # 引入時區工具函數

class ReminderScheduler:
    def __init__(self):
        self.is_running = False
        self.thread = None
        # 使用 utils/timezone.py 中的函數獲取時區
        self.timezone = get_timezone()
    
    def start(self):
        if self.is_running:
            return
        
        self.is_running = True
        
        # 安排任務
        schedule.every(15).minutes.do(self.check_morning_reminders)
        schedule.every(15).minutes.do(self.check_evening_reminders)
        
        # 啟動排程線程
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()
        
        print(f"[Scheduler] 提醒排程服務已啟動，使用時區: {self.timezone}")
    
    def run(self):
        while self.is_running:
            schedule.run_pending()
            time.sleep(60)  # 每分鐘檢查一次排程任務
    
    def get_local_time(self):
        """獲取當前的本地時間（考慮時區）"""
        # 使用 utils/timezone.py 中的函數獲取當前時間
        return get_current_time()
    
    def check_morning_reminders(self):
        now = self.get_local_time()
        # 只在早上6點到早上10點之間檢查
        if 6 <= now.hour <= 10:
            self.send_reminders('上班')
    
    def check_evening_reminders(self):
        now = self.get_local_time()
        # 只在下午5點到晚上8點之間檢查
        if 17 <= now.hour <= 20:
            self.send_reminders('下班')
    
    def send_reminders(self, reminder_type):
        print(f"[Scheduler] 檢查{reminder_type}提醒，當前時間: {self.get_local_time().strftime('%Y-%m-%d %H:%M:%S %Z')}")
        users = get_users_needing_reminder(reminder_type)
        
        for user in users:
            try:
                # 根據提醒類型準備消息
                if reminder_type == '上班':
                    message = f"⏰ {user['name']}，早安！您今天還沒有上班打卡，請記得打卡。"
                else:
                    message = f"⏰ {user['name']}，下班時間到了！您今天還沒有下班打卡，請記得打卡。"
                
                # 發送LINE消息
                success = send_line_notification(user['user_id'], message)
                
                if success:
                    # 記錄提醒日誌
                    log_reminder(user['user_id'], reminder_type)
                    print(f"[Scheduler] 已向用戶 {user['user_id']} 發送{reminder_type}提醒")
            except Exception as e:
                print(f"[Scheduler] 發送提醒給用戶 {user['user_id']} 時出錯: {str(e)}")

# 全局實例
reminder_scheduler = ReminderScheduler()
