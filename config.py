import os

LINE_LOGIN_CHANNEL_ID = os.getenv("LINE_LOGIN_CHANNEL_ID")
LINE_LOGIN_CHANNEL_SECRET = os.getenv("LINE_LOGIN_CHANNEL_SECRET")
LINE_GROUP_ID = os.getenv("LINE_GROUP_ID")
LIFF_ID = os.getenv("LIFF_ID")
GROUP_LIFF_ID = os.getenv("GROUP_LIFF_ID")
MESSAGING_CHANNEL_ACCESS_TOKEN = os.getenv("MESSAGING_CHANNEL_ACCESS_TOKEN")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
APP_URL = os.getenv("APP_URL", "https://你的應用名稱.onrender.com")
PORT = int(os.getenv("PORT", 5000))
CHECKIN_FILE = "checkin_records.json"
# 在 config.py 中添加
GROUP_MESSAGES_FILE = os.getenv("GROUP_MESSAGES_FILE", "group_messages.json")
# config.py

class Config:
    LINE_LOGIN_CHANNEL_ID = os.environ.get("LINE_LOGIN_CHANNEL_ID")
    LINE_LOGIN_CHANNEL_SECRET = os.environ.get("LINE_LOGIN_CHANNEL_SECRET")
    LINE_GROUP_ID = os.environ.get("LINE_GROUP_ID")
    MESSAGING_CHANNEL_ACCESS_TOKEN = os.environ.get("MESSAGING_CHANNEL_ACCESS_TOKEN")
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")
    LIFF_ID = os.environ.get("LIFF_ID")
    GROUP_LIFF_ID = os.environ.get("GROUP_LIFF_ID")
    APP_URL = os.environ.get("APP_URL", "https://your-default-url.onrender.com")

