import os
from dotenv import load_dotenv

load_dotenv()  # 載入 .env 檔案中的環境變數

# LINE API 設定
LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID')
LINE_LOGIN_CHANNEL_SECRET = os.environ.get('LINE_LOGIN_CHANNEL_SECRET')
LIFF_ID = os.environ.get('LIFF_ID')
MESSAGING_CHANNEL_ACCESS_TOKEN = os.environ.get('MESSAGING_CHANNEL_ACCESS_TOKEN')
LINE_GROUP_ID = os.environ.get('LINE_GROUP_ID')
