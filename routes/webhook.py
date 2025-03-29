from flask import Blueprint, request, jsonify
from datetime import datetime
import requests

from services.notification_service import send_reply, send_checkin_notification
from services.checkin_service import quick_checkin
from services.group_service import save_group_message
from config import MESSAGING_CHANNEL_ACCESS_TOKEN, APP_URL, LINE_GROUP_ID

webhook_bp = Blueprint('webhook', __name__)

# 儲存最近群組 ID（可加入更完善的狀態管理）
recent_group_id = None

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    global recent_group_id
    body = request.get_data(as_text=True)
    print(f"收到 webhook 請求: {body[:100]}...")

    try:
        events = request.json.get('events', [])
        for event in events:
            if event.get('source', {}).get('type') == 'group':
                recent_group_id = event['source']['groupId']

            if event['type'] == 'message' and event['message']['type'] == 'text':
                text = event['message']['text']
                reply_token = event['replyToken']
                source_type = event.get('source', {}).get('type')

                if text.startswith('!'):
                    command = text[1:].lower()

                    if command == '快速打卡':
                        handle_quick_checkin(event, reply_token)

                    elif command == '下載報表':
                        download_url = f"{APP_URL}/export-excel"
                        send_reply(reply_token, f"📄 點擊以下連結下載打卡報表：\n{download_url}")

                elif source_type == 'user':
                    if text in ['打卡', '打卡連結']:
                        liff_url = f"https://liff.line.me/{{LIFF_ID}}"
                        send_reply(reply_token, f"請點擊以下連結進行打卡：\n{liff_url}")
                elif source_type == 'group' and event['source']['groupId'] == LINE_GROUP_ID:
                    user_id = event['source'].get('userId')
                    if user_id:
                        profile_response = requests.get(
                            f'https://api.line.me/v2/bot/profile/{user_id}',
                            headers={
                                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
                            }
                        )
                        if profile_response.status_code == 200:
                            profile = profile_response.json()
                            user_name = profile.get('displayName', '未知用戶')
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            save_group_message(user_id, user_name, text, timestamp)

    except Exception as e:
        print(f"Webhook處理錯誤: {e}")

    return 'OK'

def handle_quick_checkin(event, reply_token):
    user_id = event['source'].get('userId')
    if not user_id:
        send_reply(reply_token, "無法獲取用戶信息，請使用 LIFF 頁面打卡")
        return

    profile_response = requests.get(
        f'https://api.line.me/v2/bot/profile/{user_id}',
        headers={'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'}
    )
    if profile_response.status_code == 200:
        profile = profile_response.json()
        display_name = profile.get('displayName', '未知用戶')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        success, message = quick_checkin(user_id, display_name)
        if success:
            send_checkin_notification(display_name, timestamp, "快速打卡", note="透過指令快速打卡")
            send_reply(reply_token, f"✅ {message}")
        else:
            send_reply(reply_token, f"❌ {message}")
    else:
        send_reply(reply_token, "無法取得使用者資料")
