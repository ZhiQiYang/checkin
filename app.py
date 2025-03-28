from flask import Flask, request, jsonify, render_template, redirect
import json
import os
import threading
import time
import requests
from datetime import datetime

app = Flask(__name__)

# 從環境變量獲取 LINE API 設置
LINE_LOGIN_CHANNEL_ID = os.environ.get('LINE_LOGIN_CHANNEL_ID')
LINE_LOGIN_CHANNEL_SECRET = os.environ.get('LINE_LOGIN_CHANNEL_SECRET')
LIFF_ID = os.environ.get('LIFF_ID')
GROUP_LIFF_ID = os.environ.get('GROUP_LIFF_ID')  # 群組互動用的LIFF ID
MESSAGING_CHANNEL_ACCESS_TOKEN = os.environ.get('MESSAGING_CHANNEL_ACCESS_TOKEN')
LINE_GROUP_ID = os.environ.get('LINE_GROUP_ID')

# Render 服務的 URL
APP_URL = os.environ.get('APP_URL', 'https://你的應用名稱.onrender.com')

# 設置 ping 的間隔時間 (秒)
PING_INTERVAL = 840  # 14分鐘，略低於 Render 的 15 分鐘休眠時間

# 儲存打卡記錄的檔案
CHECKIN_FILE = 'checkin_records.json'
# 儲存群組消息的檔案
GROUP_MESSAGES_FILE = 'group_messages.json'

# 確保檔案存在
def ensure_file_exists(filename, default_content):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump(default_content, f)

# 確保打卡記錄檔案存在
def ensure_checkin_file():
    ensure_file_exists(CHECKIN_FILE, {"records": []})

# 確保群組消息檔案存在
def ensure_group_messages_file():
    ensure_file_exists(GROUP_MESSAGES_FILE, {"messages": []})

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

# 保存群組消息
def save_group_message(user_id, user_name, message, timestamp):
    ensure_group_messages_file()
    
    with open(GROUP_MESSAGES_FILE, 'r') as f:
        data = json.load(f)
    
    # 添加新消息
    new_message = {
        "user_id": user_id,
        "user_name": user_name,
        "message": message,
        "timestamp": timestamp
    }
    
    data["messages"].append(new_message)
    
    # 只保留最近100條消息
    if len(data["messages"]) > 100:
        data["messages"] = data["messages"][-100:]
    
    with open(GROUP_MESSAGES_FILE, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# 獲取最近的群組消息
def get_recent_messages(count=20):
    ensure_group_messages_file()
    
    with open(GROUP_MESSAGES_FILE, 'r') as f:
        data = json.load(f)
    
    # 返回最近的消息
    return data["messages"][-count:]

# 發送LINE通知到群組
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
        print(f"發送LINE通知失敗: {e}")
        return False

# 發送打卡通知
def send_checkin_notification(name, time, location):
    message = f"✅ {name} 已於 {time} 完成打卡\n📍 位置: {location}"
    return send_line_message_to_group(message)

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

# 保活機制
def keep_alive():
    """定期發送請求到自己的服務來保持活躍"""
    while True:
        try:
            response = requests.get(f"{APP_URL}/ping")
            print(f"Keep-alive ping sent. Status: {response.status_code}")
        except Exception as e:
            print(f"Keep-alive ping failed: {e}")
        
        # 睡眠到下一次 ping
        time.sleep(PING_INTERVAL)

# 啟動保活線程
def start_keep_alive_thread():
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    print("Keep-alive thread started")

# 打卡頁面
@app.route('/checkin')
def checkin_page():
    return render_template('checkin.html', liff_id=LIFF_ID)

# 群組互動頁面
@app.route('/group')
def group_page():
    return render_template('group.html', liff_id=GROUP_LIFF_ID)

# LINE Login 回調
@app.route('/auth/callback')
def line_callback():
    code = request.args.get('code')
    redirect_to = request.args.get('state', 'checkin')  # 默認重定向到打卡頁面
    
    # 獲取 access token
    token_response = requests.post(
        'https://api.line.me/oauth2/v2.1/token',
        data={
            'grant_type': 'authorization_code',
            'code': code,
            'redirect_uri': f'{APP_URL}/auth/callback',
            'client_id': LINE_LOGIN_CHANNEL_ID,
            'client_secret': LINE_LOGIN_CHANNEL_SECRET
        }
    )
    
    token_data = token_response.json()
    
    # 獲取用戶信息
    profile_response = requests.get(
        'https://api.line.me/v2/profile',
        headers={'Authorization': f'Bearer {token_data["access_token"]}'}
    )
    
    profile = profile_response.json()
    
    # 這裡可以存儲用戶信息，然後重定向到相應的 LIFF 應用
    if redirect_to == 'group':
        return redirect(f'https://liff.line.me/{GROUP_LIFF_ID}')
    else:
        return redirect(f'https://liff.line.me/{LIFF_ID}')

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
        notification_sent = send_checkin_notification(display_name, timestamp, location)
        if not notification_sent:
            message += "（通知發送失敗）"
    
    return jsonify({
        'success': success,
        'message': message
    })

# 獲取群組消息API
@app.route('/api/group/messages', methods=['GET'])
def get_group_messages():
    count = int(request.args.get('count', 20))
    messages = get_recent_messages(count)
    return jsonify({
        'success': True,
        'messages': messages
    })

# 發送群組消息API
@app.route('/api/group/send', methods=['POST'])
def send_group_message():
    data = request.json
    user_id = data.get('userId')
    user_name = data.get('userName')
    message = data.get('message')
    
    if not user_id or not user_name or not message:
        return jsonify({
            'success': False,
            'message': '缺少必要參數'
        })
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 構建發送到群組的消息
    group_message = f"💬 {user_name}:\n{message}"
    
    # 發送到 LINE 群組
    sent = send_line_message_to_group(group_message)
    
    if sent:
        # 保存消息記錄
        save_group_message(user_id, user_name, message, timestamp)
        return jsonify({
            'success': True,
            'message': '消息已發送'
        })
    else:
        return jsonify({
            'success': False,
            'message': '發送失敗'
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
                source_type = event.get('source', {}).get('type')
                
                # 處理來自用戶的私聊消息
                if source_type == 'user':
                    if text == '打卡' or text == '打卡連結':
                        liff_url = f'https://liff.line.me/{LIFF_ID}'
                        send_reply(reply_token, f"請點擊以下連結進行打卡：\n{liff_url}")
                    elif text == '群組聊天' or text == '群組互動':
                        group_url = f'https://liff.line.me/{GROUP_LIFF_ID}'
                        send_reply(reply_token, f"請點擊以下連結進入群組互動頁面：\n{group_url}")
                
                # 處理來自群組的消息
                elif source_type == 'group':
                    group_id = event['source']['groupId']
                    
                    # 如果是目標群組的消息
                    if group_id == LINE_GROUP_ID:
                        # 嘗試獲取用戶ID（某些情況下可能無法獲取）
                        user_id = event['source'].get('userId')
                        
                        if user_id:
                            # 獲取用戶資料
                            profile_response = requests.get(
                                f'https://api.line.me/v2/bot/profile/{user_id}',
                                headers={
                                    'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
                                }
                            )
                            
                            if profile_response.status_code == 200:
                                profile = profile_response.json()
                                user_name = profile.get('displayName', '未知用戶')
                                
                                # 保存群組消息
                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                save_group_message(user_id, user_name, text, timestamp)
                            
                        # 處理特定群組指令
                        if text.startswith('!'):
                            command = text[1:].lower()
                            
                            if command == 'help':
                                help_message = (
                                    "📢 群組互動機器人指令:\n"
                                    "!help - 顯示此幫助信息\n"
                                    "!打卡 - 獲取打卡連結\n"
                                    "!互動 - 獲取群組互動頁面連結"
                                )
                                send_reply(reply_token, help_message)
                            
                            elif command == '打卡':
                                liff_url = f'https://liff.line.me/{LIFF_ID}'
                                send_reply(reply_token, f"請點擊以下連結進行打卡：\n{liff_url}")
                            
                            elif command == '互動':
                                group_url = f'https://liff.line.me/{GROUP_LIFF_ID}'
                                send_reply(reply_token, f"請點擊以下連結進入群組互動頁面：\n{group_url}")
    
    except Exception as e:
        print(f"Webhook處理錯誤: {e}")
    
    return 'OK'

# 健康檢查
@app.route('/')
def index():
    return "打卡系統運行中!"

# 健康檢查/ping 路由
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}), 200

if __name__ == '__main__':
    # 啟動保活線程
    start_keep_alive_thread()
    
    # 啟動 Flask 應用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
