from flask import Flask, request, jsonify, render_template
import json
import os
import requests
from datetime import datetime
from config import *

app = Flask(__name__)

# 儲存打卡記錄的檔案
CHECKIN_FILE = 'checkin_records.json'

# 確保打卡記錄檔案存在
def ensure_checkin_file():
    if not os.path.exists(CHECKIN_FILE):
        with open(CHECKIN_FILE, 'w') as f:
            json.dump({"records": []}, f)

# 儲存打卡記錄
def save_checkin(user_id, name, timestamp, location):
    ensure_checkin_file()
    
    with open(CHECKIN_FILE, 'r') as f:
        data = json.load(f)
    
    # 檢查今天是否已經打卡
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 檢查是否已經打卡
    for record in data["records"]:
        if record["user_id"] == user_id and record["date"] == today:
            return False, "今天已經打卡過了"
    
    # 添加新記錄
    new_record = {
        "user_id": user_id,
        "name": name,
        "date": today,
        "time": timestamp,
        "location": location
    }
    
    data["records"].append(new_record)
    
    with open(CHECKIN_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    return True, "打卡成功"

# 發送LINE通知
def send_line_notification(name, time, location):
    message = f"✅ {name} 已於 {time} 完成打卡\n📍 位置: {location}"
    
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
        print(f"發送LINE通知失敗: {e}")
        return False

# 打卡頁面
@app.route('/checkin')
def checkin_page():
    return render_template('checkin.html', liff_id=LIFF_ID)

# 打卡API
@app.route('/api/checkin', methods=['POST'])
def process_checkin():
    data = request.json
    user_id = data.get('userId')
    display_name = data.get('displayName')
    location = data.get('location', '未提供位置')
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 儲存打卡記錄
    success, message = save_checkin(user_id, display_name, timestamp, location)
    
    if success:
        # 發送LINE通知
        notification_sent = send_line_notification(display_name, timestamp, location)
        if not notification_sent:
            message += "（通知發送失敗）"
    
    return jsonify({
        'success': success,
        'message': message
    })

# LINE Webhook 處理
@app.route('/webhook', methods=['POST'])
def webhook():
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    try:
        events = request.json.get('events', [])
        for event in events:
            if event['type'] == 'message' and event['message']['type'] == 'text':
                text = event['message']['text']
                reply_token = event['replyToken']
                
                if text == '打卡' or text == '打卡連結':
                    liff_url = f'https://liff.line.me/{LIFF_ID}'
                    send_reply(reply_token, f"請點擊以下連結進行打卡：\n{liff_url}")
    
    except Exception as e:
        print(f"Webhook處理錯誤: {e}")
    
    return 'OK'

# 回覆訊息
def send_reply(reply_token, text):
    try:
        requests.post(
            'https://api.line.me/v2/bot/message/reply',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json={
                'replyToken': reply_token,
                'messages': [{'type': 'text', 'text': text}]
            }
        )
    except Exception as e:
        print(f"回覆訊息失敗: {e}")

# 健康檢查
@app.route('/')
def index():
    return "打卡系統運行中!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
