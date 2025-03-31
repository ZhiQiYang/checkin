# config.py
import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class Config:
    # 所有配置變數都放在這裡
    LINE_LOGIN_CHANNEL_ID = os.environ.get("LINE_LOGIN_CHANNEL_ID")
    LINE_LOGIN_CHANNEL_SECRET = os.environ.get("LINE_LOGIN_CHANNEL_SECRET")
    LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
    MESSAGING_CHANNEL_ACCESS_TOKEN = os.environ.get("MESSAGING_CHANNEL_ACCESS_TOKEN")
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")
    LIFF_ID = os.environ.get("LIFF_ID")
    GROUP_LIFF_ID = os.environ.get("GROUP_LIFF_ID")
    APP_URL = os.environ.get("APP_URL", "https://checkin-ciqs.onrender.com")
    PORT = int(os.environ.get("PORT", 5000))

    # 檔案配置 - 檢查環境變數，如果不存在則使用永久存儲路徑
    # 注意：在 Render 平台上，應使用永久存儲路徑，因為臨時路徑在重啟後會丟失數據
    CHECKIN_FILE = os.environ.get("CHECKIN_FILE", "checkin_records.json")
    GROUP_MESSAGES_FILE = os.environ.get("GROUP_MESSAGES_FILE", "group_messages.json")
    
    # 資料庫配置
    DB_PATH = os.environ.get("DB_PATH", "checkin.db")
    
    # 應用程序配置
    DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
    SECRET_KEY = os.environ.get("SECRET_KEY", os.urandom(24).hex())
    
    # 保活配置
    KEEP_ALIVE_INTERVAL = int(os.environ.get("KEEP_ALIVE_INTERVAL", 300))  # 默認5分鐘
    
    # 時區設置 (默認為台灣時區)
    TIMEZONE = os.environ.get("TIMEZONE", "Asia/Taipei")  
