import logging
import requests
from config import Config
import sqlite3

logger = logging.getLogger(__name__)

class UserService:
    """處理用戶相關邏輯的服務類"""
    
    @staticmethod
    def get_line_profile(user_id):
        """獲取LINE用戶資料"""
        if not user_id:
            return None
            
        try:
            profile_response = requests.get(
                f'https://api.line.me/v2/bot/profile/{user_id}',
                headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
            )
            
            if profile_response.status_code == 200:
                return profile_response.json()
            else:
                logger.warning(f"獲取LINE用戶資料失敗: {profile_response.status_code} {profile_response.text}")
                return None
        except Exception as e:
            logger.error(f"獲取LINE用戶資料時出錯: {str(e)}")
            return None
    
    @staticmethod
    def get_user_info(user_id):
        """獲取用戶資訊，如果不存在則根據LINE資料創建用戶"""
        if not user_id:
            return None
            
        try:
            # 從數據庫獲取用戶信息
            conn = sqlite3.connect(Config.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if user:
                return dict(user)
            
            # 用戶不存在，嘗試從LINE獲取資料
            profile = UserService.get_line_profile(user_id)
            if profile:
                display_name = profile.get('displayName', '')
                
                # 創建新用戶
                cursor.execute(
                    "INSERT INTO users (user_id, name, display_name) VALUES (?, ?, ?)",
                    (user_id, display_name, display_name)
                )
                conn.commit()
                
                # 重新獲取用戶信息
                cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                user = cursor.fetchone()
                if user:
                    return dict(user)
            
            conn.close()
            return None
            
        except Exception as e:
            logger.error(f"獲取/創建用戶信息時出錯: {str(e)}")
            return None
    
    @staticmethod
    def update_user_settings(user_id, settings):
        """更新用戶設置"""
        if not user_id or not settings:
            return False
            
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            cursor = conn.cursor()
            
            # 檢查用戶是否存在
            cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            
            if not user:
                # 用戶不存在，先創建用戶
                profile = UserService.get_line_profile(user_id)
                if profile:
                    display_name = profile.get('displayName', '')
                    
                    cursor.execute(
                        "INSERT INTO users (user_id, name, display_name) VALUES (?, ?, ?)",
                        (user_id, display_name, display_name)
                    )
                    conn.commit()
                else:
                    # 無法獲取用戶資料，使用默認值
                    cursor.execute(
                        "INSERT INTO users (user_id, name, display_name) VALUES (?, ?, ?)",
                        (user_id, '未知用戶', '未知用戶')
                    )
                    conn.commit()
            
            # 更新用戶設置
            # 這裡假設settings是一個字典，包含要更新的欄位和值
            update_fields = []
            update_values = []
            
            for key, value in settings.items():
                if key != 'user_id':  # 防止更新主鍵
                    update_fields.append(f"{key} = ?")
                    update_values.append(value)
            
            if not update_fields:
                return False
                
            update_sql = f"UPDATE users SET {', '.join(update_fields)} WHERE user_id = ?"
            update_values.append(user_id)
            
            cursor.execute(update_sql, update_values)
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"更新用戶設置時出錯: {str(e)}")
            return False
    
    @staticmethod
    def get_all_active_users():
        """獲取所有用戶"""
        try:
            conn = sqlite3.connect(Config.DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 獲取所有用戶
            cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            
            conn.close()
            
            return [dict(user) for user in users]
            
        except Exception as e:
            logger.error(f"獲取用戶時出錯: {str(e)}")
            return [] 