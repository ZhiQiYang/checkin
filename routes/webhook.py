from flask import Blueprint, request, jsonify
from datetime import datetime
import requests

from services.notification_service import send_reply, send_checkin_notification
from services.checkin_service import quick_checkin
from services.group_service import save_group_message
from config import Config

webhook_bp = Blueprint('webhook', __name__)

# 修改這裡，使用 Config 類
@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    # ... 其他代碼 ...
    # 修改所有使用 MESSAGING_CHANNEL_ACCESS_TOKEN, APP_URL, LINE_GROUP_ID 的地方
    # 將它們改為 Config.MESSAGING_CHANNEL_ACCESS_TOKEN, Config.APP_URL, Config.LINE_GROUP_ID
