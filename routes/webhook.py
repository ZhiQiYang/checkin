from flask import Blueprint, request, jsonify
from datetime import datetime
import requests
from services.notification_service import send_reply, send_checkin_notification
from services.checkin_service import quick_checkin
from services.group_service import save_group_message
from config import Config

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
                        download_url = f"{Config.APP_URL}/export-excel"
                        send_reply(reply_token, f"📄 點擊以下連結下載打卡報表：\n{download_url}")

                elif source_type == 'user':
                    if text in ['打卡', '打卡連結']:
                        liff_url = f"https://liff.line.me/{Config.LIFF_ID}"
                        send_reply(reply_token, f"請點擊以下連結進行打卡：\n{liff_url}")
                elif source_type == 'group' and event['source']['groupId'] == Config.LINE_GROUP_ID:
                    user_id = event['source'].get('userId')
                    if user_id:
                        profile_response = requests.get(
                            f'https://api.line.me/v2/bot/profile/{user_id}',
                            headers={
                                'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
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

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    print("正在處理 webhook 請求")
    body = request.get_data(as_text=True)
    print(f"請求內容: {body}")
    
    try:
        # 直接測試發送回覆
        events = request.json.get('events', [])
        for event in events:
            if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                text = event.get('message', {}).get('text', '')
                if text == '!快速打卡':
                    reply_token = event.get('replyToken')
                    print(f"嘗試直接回覆 token: {reply_token}")
                    # 先發送簡單回覆測試基本功能
                    send_reply(reply_token, "收到打卡指令，處理中...")
                    # 其他處理...
    except Exception as e:
        print(f"處理過程出錯: {str(e)}")
    
    return 'OK'

@webhook_bp.route('/test-line-api', methods=['GET'])
def test_line_api():
    try:
        response = requests.get(
            'https://api.line.me/v2/bot/info',
            headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
        )
        return jsonify({
            "status": response.status_code,
            "response": response.text
        })
    except Exception as e:
        return jsonify({"error": str(e)})


def handle_quick_checkin(event, reply_token):
    user_id = event['source'].get('userId')
    if not user_id:
        send_reply(reply_token, "無法獲取用戶信息，請使用 LIFF 頁面打卡")
        return

    profile_response = requests.get(
        f'https://api.line.me/v2/bot/profile/{user_id}',
        headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
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
