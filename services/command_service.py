import re
import logging
import traceback
from datetime import datetime
from config import Config
from services.notification_service import send_reply, send_line_notification
from services.checkin_service import quick_checkin
from services.vocabulary_service import get_daily_words, format_daily_words
from services.user_service import UserService
from utils.timezone import get_date_string
from models import ReminderSetting
import sqlite3

logger = logging.getLogger(__name__)

class CommandService:
    """處理Line Bot指令的服務類"""
    
    @staticmethod
    def handle_command(event, text):
        """處理用戶發送的命令，返回處理結果"""
        reply_token = event.get('replyToken')
        user_id = event['source'].get('userId') if 'source' in event else None
        
        # 記錄命令和用戶ID
        logger.info(f"收到命令: {text}, 用戶ID: {user_id}")
        
        # 如果是查詢ID命令
        if text == "查詢ID":
            if user_id:
                send_reply(reply_token, f"您的用戶 ID 是: {user_id}")
                return 'OK'
            return None
            
        # 命令處理邏輯
        if text.startswith('!'):
            command = text[1:].lower()  # 移除開頭的!並轉小寫
            
            # 單字學習相關命令
            if command == '今日單字學習' or command in ['單字學習', '學習單字', '今日單字']:
                return CommandService.handle_vocabulary_command(event, reply_token, user_id)
                
            # 提醒設置相關命令
            set_morning_reminder_match = re.match(r'^設定上班提醒 *(\d{1,2}:\d{2})$', command)
            if set_morning_reminder_match:
                time_str = set_morning_reminder_match.group(1)
                return CommandService.handle_set_reminder(event, reply_token, "morning", time_str)
                
            set_evening_reminder_match = re.match(r'^設定下班提醒 *(\d{1,2}:\d{2})$', command)
            if set_evening_reminder_match:
                time_str = set_evening_reminder_match.group(1)
                return CommandService.handle_set_reminder(event, reply_token, "evening", time_str)
                
            if command == '設定提醒':
                return CommandService.handle_show_reminder_settings(event, reply_token, user_id)
                
            # 打卡相關命令
            if command == '快速打卡' or command == '上班打卡':
                return CommandService.handle_quick_checkin(event, reply_token, "上班")
            elif command == '下班打卡':
                return CommandService.handle_quick_checkin(event, reply_token, "下班")
            elif command == '打卡':
                return CommandService.handle_quick_checkin(event, reply_token)
            elif command == '打卡報表':
                return CommandService.handle_checkin_report(event, reply_token, user_id)
                
            # 幫助命令
            elif command == '幫助':
                return CommandService.handle_help_command(event, reply_token)
                
            # 測試提醒命令
            elif command == '測試提醒':
                return CommandService.handle_test_reminder(event, reply_token, user_id)
                
            # 系統狀態命令
            elif command == '系統狀態':
                return CommandService.handle_system_status(event, reply_token)
                
        return None  # 沒有處理任何命令
    
    @staticmethod
    def handle_vocabulary_command(event, reply_token, user_id):
        """處理單字學習相關命令"""
        if not user_id:
            send_reply(reply_token, "❌ 無法獲取用戶ID，請稍後再試")
            return 'OK'
            
        try:
            today_date = get_date_string()
            
            # 嘗試獲取詞彙
            logger.info(f"嘗試為用戶 {user_id} 獲取 {today_date} 的單字")
            daily_words = get_daily_words(today_date, user_id)
            
            if not daily_words or len(daily_words) == 0:
                logger.warning("獲取詞彙返回空列表，使用備用詞彙")
                # 使用備用詞彙
                daily_words = [
                    {'english': 'reliability', 'chinese': '可靠性；可信度', 'difficulty': 2},
                    {'english': 'dedication', 'chinese': '奉獻；專注', 'difficulty': 2},
                    {'english': 'proficiency', 'chinese': '熟練；精通', 'difficulty': 2}
                ]
            
            # 格式化詞彙
            vocab_message = format_daily_words(daily_words)
            
            # 添加版本號，幫助調試
            vocab_message += "\n\n系統版本: v2.2"
            
            # 發送回覆
            send_reply(reply_token, vocab_message)
        except Exception as e:
            logger.error(f"處理單字學習命令出錯: {str(e)}")
            logger.debug(traceback.format_exc())  # 記錄完整錯誤追踪
            
            # 返回更友好的錯誤信息
            error_message = "📚 今日單字學習\n正在準備您的詞彙，請稍後再試\n\n如果問題持續出現，請使用「!上班打卡」命令後查看回覆中的單字學習部分"
            send_reply(reply_token, error_message)
        
        return 'OK'
    
    @staticmethod
    def handle_set_reminder(event, reply_token, reminder_type, time_str):
        """設置提醒時間"""
        user_id = event['source'].get('userId')
        if not user_id:
            send_reply(reply_token, "❌ 無法獲取用戶ID，請稍後再試")
            return 'OK'
        
        # 驗證時間格式
        try:
            hours, minutes = map(int, time_str.split(':'))
            if hours < 0 or hours > 23 or minutes < 0 or minutes > 59:
                send_reply(reply_token, f"❌ 時間格式不正確，請使用24小時制（例如：09:00）")
                return 'OK'
        except ValueError:
            send_reply(reply_token, f"❌ 時間格式不正確，請使用HH:MM格式")
            return 'OK'
        
        # 更新提醒設置
        settings = ReminderSetting.get_by_user_id(user_id) or {}
        
        if reminder_type == "morning":
            settings['checkin_time'] = time_str
            ReminderSetting.update_settings(user_id, settings)
            send_reply(reply_token, f"✅ 已將上班提醒時間設為 {time_str}")
        elif reminder_type == "evening":
            settings['checkout_time'] = time_str
            ReminderSetting.update_settings(user_id, settings)
            send_reply(reply_token, f"✅ 已將下班提醒時間設為 {time_str}")
        
        return 'OK'
    
    @staticmethod
    def handle_show_reminder_settings(event, reply_token, user_id):
        """顯示當前提醒設置"""
        if not user_id:
            send_reply(reply_token, "❌ 無法獲取用戶ID，請稍後再試")
            return 'OK'
            
        # 獲取當前提醒設置
        settings = ReminderSetting.get_by_user_id(user_id)
        if not settings:
            send_reply(reply_token, "❌ 無法獲取提醒設置，請稍後再試")
            return 'OK'
            
        morning_time = settings.get('checkin_time', '09:00')
        evening_time = settings.get('checkout_time', '18:00')
        checkin_reminder = settings.get('checkin_reminder', True)
        checkout_reminder = settings.get('checkout_reminder', True)
        weekly_report = settings.get('weekly_report', False)
        monthly_report = settings.get('monthly_report', False)
        
        checkin_status = "啟用" if checkin_reminder else "停用"
        checkout_status = "啟用" if checkout_reminder else "停用"
        weekly_status = "啟用" if weekly_report else "停用"
        monthly_status = "啟用" if monthly_report else "停用"
        
        # 綜合提醒設置信息
        settings_message = (
            f"⏰ 當前提醒設置：\n"
            f"- 上班提醒：{checkin_status}\n"
            f"- 上班提醒時間：{morning_time}\n"
            f"- 下班提醒：{checkout_status}\n"
            f"- 下班提醒時間：{evening_time}\n"
            f"- 週報告：{weekly_status}\n"
            f"- 月報告：{monthly_status}\n\n"
            f"您可以使用以下指令修改設置：\n"
            f"!設定上班提醒 HH:MM\n"
            f"!設定下班提醒 HH:MM\n"
            f"或點擊以下連結進行詳細設置：\n"
            f"{Config.APP_URL}/reminder-settings?userId={user_id}"
        )
        
        send_reply(reply_token, settings_message)
        return 'OK'
    
    @staticmethod
    def handle_quick_checkin(event, reply_token, checkin_type=None):
        """處理快速打卡命令"""
        try:
            result = quick_checkin(event, checkin_type)
            send_reply(reply_token, result)
        except Exception as e:
            logger.error(f"快速打卡出錯: {str(e)}")
            send_reply(reply_token, f"❌ 打卡失敗，請稍後再試。錯誤: {str(e)}")
        return 'OK'
    
    @staticmethod
    def handle_checkin_report(event, reply_token, user_id):
        """處理打卡報表命令"""
        if not user_id:
            send_reply(reply_token, "❌ 無法獲取用戶ID，請稍後再試")
            return 'OK'
            
        report_url = f"{Config.APP_URL}/personal-history?userId={user_id}"
        send_reply(reply_token, f"📊 您的打卡報表：\n{report_url}")
        return 'OK'
    
    @staticmethod
    def handle_help_command(event, reply_token):
        """處理幫助命令"""
        help_text = (
            "📱 打卡系統指令說明：\n"
            "!上班打卡 - 快速完成上班打卡\n"
            "!下班打卡 - 快速完成下班打卡\n"
            "!快速打卡 - 快速完成上班打卡（等同於!上班打卡）\n"
            "!打卡報表 - 查看打卡統計報表\n"
            "!今日單字學習 - 獲取今日英文單字\n"
            "!設定提醒 - 查看與設定提醒時間\n"
            "!設定上班提醒 HH:MM - 設定上班提醒時間\n"
            "!設定下班提醒 HH:MM - 設定下班提醒時間\n"
            "!測試提醒 - 發送測試提醒\n"
            "!系統狀態 - 查看系統運行狀態\n"
            "!管理指令 - 顯示管理員指令列表\n"
            "打卡 - 獲取打卡頁面連結\n"
            "其他問題請聯繫管理員"
        )
        send_reply(reply_token, help_text)
        return 'OK'
    
    @staticmethod
    def handle_test_reminder(event, reply_token, user_id):
        """處理測試提醒命令"""
        if not user_id:
            send_reply(reply_token, "❌ 無法獲取用戶ID，請稍後再試")
            return 'OK'
            
        try:
            # 使用UserService獲取用戶資料
            user_info = UserService.get_user_info(user_id)
            
            if user_info:
                # 發送測試提醒
                display_name = user_info.get('name', '用戶')
                message = f"⏰ 測試提醒 - {display_name}，這是一條測試提醒消息。"
                send_line_notification(user_id, message)
                send_reply(reply_token, "✅ 測試提醒已發送，請查看您的LINE通知")
            else:
                # 無法獲取用戶資料，使用通用消息
                message = "⏰ 測試提醒 - 這是一條測試提醒消息。"
                send_line_notification(user_id, message)
                send_reply(reply_token, "✅ 測試提醒已發送，請查看您的LINE通知")
        except Exception as e:
            logger.error(f"發送測試提醒時出錯: {str(e)}")
            send_reply(reply_token, f"❌ 發送提醒時出錯: {str(e)[:30]}...")
        
        return 'OK'
    
    @staticmethod
    def handle_system_status(event, reply_token):
        """處理系統狀態命令"""
        try:
            status_text = f"系統狀態報告 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
            
            # 檢查數據庫
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            
            # 檢查打卡記錄數
            c.execute("SELECT COUNT(*) FROM checkin_records")
            checkin_count = c.fetchone()[0]
            status_text += f"✓ 打卡記錄總數: {checkin_count} 筆\n"
            
            # 檢查今日打卡數
            today = datetime.now().strftime("%Y-%m-%d")
            c.execute("SELECT COUNT(*) FROM checkin_records WHERE date = ?", (today,))
            today_count = c.fetchone()[0]
            status_text += f"✓ 今日打卡數: {today_count} 筆\n"
            
            # 檢查用戶數
            c.execute("SELECT COUNT(*) FROM users")
            user_count = c.fetchone()[0]
            status_text += f"✓ 用戶總數: {user_count} 人\n"
            
            # 檢查最近一次打卡
            c.execute("SELECT name, date, time, checkin_type FROM checkin_records ORDER BY id DESC LIMIT 1")
            last_record = c.fetchone()
            if last_record:
                status_text += f"✓ 最近打卡: {last_record[0]} 於 {last_record[1]} {last_record[2]} {last_record[3]}打卡\n"
            
            conn.close()
            
            # 添加系統版本信息
            status_text += f"✓ 系統運行正常\n✓ 版本: 2.2"
            
            send_reply(reply_token, status_text)
        except Exception as e:
            logger.error(f"獲取系統狀態時出錯: {str(e)}")
            send_reply(reply_token, f"❌ 獲取系統狀態時出錯: {str(e)[:30]}...")
        
        return 'OK' 