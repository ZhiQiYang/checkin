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

def send_checkin_notification(name, time, location, note=None, latitude=None, longitude=None):
    message = f"✅ {name} 已於 {time} 完成打卡\n📍 位置: {location}"
    if note:
        message += f"\n📝 備註: {note}"
    if latitude and longitude:
        map_link = f"https://www.google.com/maps?q={latitude},{longitude}"
        message += f"\n🗺️ 查看地圖: {map_link}"
    return send_line_message_to_group(message)

def send_reply(reply_token, text):
    try:
        requests.post(
            'https://api.line.me/v2/bot/message/reply',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json={
                'replyToken': reply_token,
                'messages': [{'type': 'text', 'text': text}]
            }
        )
    except Exception as e:
        print(f"[通知錯誤] 回覆訊息失敗: {e}")

def send_reply_raw(reply_token, messages):
    """
    發送自定義格式的回覆消息
    
    Args:
        reply_token: LINE 回覆令牌
        messages: 消息列表，每個元素都是一個符合 LINE API 消息格式的字典
    """
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/reply',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json={
                'replyToken': reply_token,
                'messages': messages
            }
        )
        if response.status_code != 200:
            print(f"[通知錯誤] 回覆消息失敗: {response.status_code} {response.text}")
            return False
        return True
    except Exception as e:
        print(f"[通知錯誤] 回覆消息失敗: {e}")
        return False

# 發送LINE個人通知函數
def send_line_notification(user_id, message):
    """發送LINE個人通知"""
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/message/push',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json={
                'to': user_id,
                'messages': [{'type': 'text', 'text': message}]
            }
        )
        return response.status_code == 200
    except Exception as e:
        print(f"[通知錯誤] 發送個人通知失敗: {e}")
        return False

# 添加别名（向後兼容），改名避免衝突
send_line_group_notification = send_line_message_to_group
