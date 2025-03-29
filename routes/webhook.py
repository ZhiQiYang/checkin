from flask import Blueprint, request, jsonify
from datetime import datetime
import requests

from services.notification_service import send_checkin_notification, send_line_message_to_group, send_reply
from services.checkin_service import process_checkin
from services.group_service import save_group_message
from utils.file_helper import save_json, load_json
from config import MESSAGING_CHANNEL_ACCESS_TOKEN, APP_URL, LINE_GROUP_ID

webhook_bp = Blueprint('webhook', __name__)

recent_group_id = None  # 用於 get-group-id 工具

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    global recent_group_id
    body = request.get_data(as_text=True)
    print(f"[Webhook] Received: {body[:100]}...")

    try:
        events = request.json.get('events', [])
        for event in events:
            source_type = event.get('source', {}).get('type')
            user_id = event['source'].get('userId')
            text = event['message']['text'] if event['type'] == 'message' else ''
            reply_token = event.get('replyToken')

            # 更新最近群組 ID
            if source_type == 'group':
                recent_group_id = event['source']['groupId']

            # 儲存群組對話
            if source_type == 'group' and text and user_id:
                profile_response = requests.get(
                    f'https://api.line.me/v2/bot/profile/{user_id}',
                    headers={'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'}
                )
                if profile_response.status_code == 200:
                    profile = profile_response.json()
                    user_name = profile.get('displayName', '未知用戶')
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    save_group_message(user_id, user_name, text, timestamp)

            # 處理指令
            if text.startswith('!'):
                command = text[1:].strip().lower()

                if command == '快速打卡':
                    if not user_id:
                        send_reply(reply_token, "無法獲取用戶信息")
                        continue
                    profile = requests.get(
                        f'https://api.line.me/v2/bot/profile/{user_id}',
                        headers={'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'}
                    ).json()
                    display_name = profile.get('displayName', '未知用戶')
                    success, message, timestamp = process_checkin(user_id, display_name, "快速打卡", note="透過指令快速打卡")
                    if success:
                        send_checkin_notification(display_name, timestamp, "快速打卡", note="透過指令快速打卡")
                    send_reply(reply_token, f"{'✅' if success else '❌'} {message}")

                elif command == '打卡報表':
                    data = load_json('checkin_records.json')
                    today = datetime.now().strftime("%Y-%m-%d")
                    records = [r for r in data['records'] if r['date'] == today]
                    if not records:
                        send_reply(reply_token, "今日尚無打卡記錄")
                        continue
                    report = "📊 今日打卡報表:\n\n"
                    for idx, r in enumerate(records, 1):
                        report += f"{idx}. {r['name']} - {r['time']}\n📍 {r['location']}"
                        if r.get('note'):
                            report += f"\n📝 {r['note']}"
                        if r.get('coordinates'):
                            lat, lng = r['coordinates'].get('latitude'), r['coordinates'].get('longitude')
                            if lat and lng:
                                report += f"\n🗺️ https://www.google.com/maps?q={lat},{lng}"
                        report += "\n\n"
                    send_reply(reply_token, report[:4000])

                elif command in ['歷史', '打卡歷史']:
                    if user_id:
                        history_url = f"{APP_URL}/personal-history?userId={user_id}"
                        send_reply(reply_token, f"請點擊以下連結查看您的打卡歷史：\n{history_url}")

                elif command == '下載報表':
                    send_reply(reply_token, f"📄 點擊以下連結下載打卡報表：\n{APP_URL}/export-excel")

                elif command == '幫助':
                    help_msg = (
                        "📱 打卡系統使用說明:\n\n"
                        "1. 發送 !快速打卡\n"
                        "2. 發送 !打卡報表\n"
                        "3. 發送 !歷史 或 !打卡歷史\n"
                        "4. 發送 !下載報表\n"
                        "5. 發送 !幫助 顯示此訊息"
                    )
                    send_reply(reply_token, help_msg)

    except Exception as e:
        print(f"[Webhook Error] {e}")
    return 'OK'
