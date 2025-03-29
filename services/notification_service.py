import requests
from config import Config

def send_line_message_to_group(message):
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json={
                'to': Config.LINE_GROUP_ID,
                'messages': [{'type': 'text', 'text': message}]
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[通知錯誤] 發送群組訊息失敗: {e}")
        return False
