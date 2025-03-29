import requests
from config import MESSAGING_CHANNEL_ACCESS_TOKEN, LINE_GROUP_ID

def send_line_message_to_group(message):
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json={
                'to': LINE_GROUP_ID,
                'messages': [{'type': 'text', 'text': message}]
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[LINE ERROR] {e}")
        return False

def send_checkin_notification(name, time, location, note=None, latitude=None, longitude=None):
    message = f"✅ {name} 已於 {time} 完成打卡\n📍 位置: {location}"
    if note:
        message += f"\n📝 備註: {note}"
    if latitude and longitude:
        message += f"\n🗺️ 查看地圖: https://www.google.com/maps?q={latitude},{longitude}"
    return send_line_message_to_group(message)
