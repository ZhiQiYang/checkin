import os

class Config:
    APP_URL = os.environ.get('APP_URL', 'https://你的應用.onrender.com')
    PORT = int(os.environ.get('PORT', 5000))
    PING_INTERVAL = 840  # 14 minutes
    LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID')
    LINE_LOGIN_CHANNEL_SECRET = os.environ.get('LINE_LOGIN_CHANNEL_SECRET')
    LINE_GROUP_ID = os.environ.get('LINE_GROUP_ID')
    MESSAGING_CHANNEL_ACCESS_TOKEN = os.environ.get('MESSAGING_CHANNEL_ACCESS_TOKEN')
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')
    LIFF_ID = os.environ.get('LIFF_ID')
    GROUP_LIFF_ID = os.environ.get('GROUP_LIFF_ID')
