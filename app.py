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

# 存儲最近的群組ID
recent_group_id = None

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

# 臨時路由用於獲取群組ID
@app.route('/get-group-id', methods=['GET'])
def get_group_id():
    return """
    <html>
    <body>
        <h1>群組ID獲取工具</h1>
        <p>請發送一條消息到包含機器人的群組，然後查看此頁面的結果。</p>
        <p>最近的群組ID: <strong id="groupId">等待消息...</strong></p>
        <script>
            setInterval(function() {
                fetch('/api/recent-group-id')
                    .then(response => response.json())
                    .then(data => {
                        if (data.groupId) {
                            document.getElementById('groupId').textContent = data.groupId;
                        }
                    });
            }, 5000);
        </script>
    </body>
    </html>
    """

# 提供最近的群組ID
@app.route('/api/recent-group-id', methods=['GET'])
def api_recent_group_id():
    return jsonify({"groupId": recent_group_id})

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

# LINE Webhook 處理 (合併了獲取群組ID的功能)
@app.route('/webhook', methods=['POST'])
def webhook():
    global recent_group_id  # 使用全局變量存儲最近的群組ID
    signature = request.headers.get('X-Line-Signature', '')
    body = request.get_data(as_text=True)
    
    print(f"收到 webhook 請求: {body[:100]}...")  # 只打印前100個字符避免日誌過長
    
    try:
        events = request.json.get('events', [])
        for event in events:
            # 獲取群組ID (用於 get-group-id 工具)
            if event.get('source', {}).get('type') == 'group':
                recent_group_id = event['source']['groupId']
                print(f"Found group ID: {recent_group_id}")
            
            # 正常的消息處理邏輯
            if event['type'] == 'message' and event['message']['type'] == 'text':
                text = event['message']['text']
                reply_token = event['replyToken']
                source_type = event.get('source', {}).get('type')
                
                # 處理 Rich Menu 消息
                if text.startswith('!'):
                    command = text[1:].lower()
                    
                    # 快速打卡
                    if command == '快速打卡':
                        user_id = event['source'].get('userId')
                        if not user_id:
                            send_reply(reply_token, "無法獲取用戶信息，請使用 LIFF 頁面打卡")
                            continue
                            
                        # 獲取用戶資料
                        profile_response = requests.get(
                            f'https://api.line.me/v2/bot/profile/{user_id}',
                            headers={
                                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
                            }
                        )
                        
                        if profile_response.status_code == 200:
                            profile = profile_response.json()
                            display_name = profile.get('displayName', '未知用戶')
                            
                            # 進行打卡
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            success, message = save_checkin(user_id, display_name, timestamp, "快速打卡")
                            
                            if success:
                                send_checkin_notification(display_name, timestamp, "快速打卡")
                                send_reply(reply_token, f"✅ {message}")
                            else:
                                send_reply(reply_token, f"❌ {message}")
                        else:
                            send_reply(reply_token, "無法獲取用戶資料，請使用 LIFF 頁面打卡")
                    
                    # 打卡報表
                    elif command == '打卡報表':
                        # 獲取今日打卡記錄
                        ensure_checkin_file()
                        with open(CHECKIN_FILE, 'r') as f:
                            data = json.load(f)
                        
                        today = datetime.now().strftime("%Y-%m-%d")
                        today_records = [r for r in data['records'] if r['date'] == today]
                        
                        if not today_records:
                            send_reply(reply_token, "今日尚無打卡記錄")
                        else:
                            report = "📊 今日打卡報表:\n\n"
                            for idx, record in enumerate(today_records, 1):
                                report += f"{idx}. {record['name']} - {record['time']}\n"
                            
                            send_reply(reply_token, report)
                    
                    # 幫助
                    elif command == '幫助':
                        help_message = (
                            "📱 打卡系統使用說明:\n\n"
                            "1. 點擊選單中的「打卡」按鈕進行定位打卡\n"
                            "2. 點擊「群組互動」進入群組聊天室\n"
                            "3. 發送「!快速打卡」可直接打卡\n"
                            "4. 發送「!打卡報表」查看今日打卡情況\n"
                            "5. 發送「!幫助」查看此幫助訊息"
                        )
                        send_reply(reply_token, help_message)
                
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
    
    except Exception as e:
        print(f"Webhook處理錯誤: {e}")
    
    return 'OK'

# 建立 Rich Menu
def create_rich_menu():
    try:
        # 定義 Rich Menu 結構
        rich_menu_data = {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": True,
            "name": "打卡系統選單",
            "chatBarText": "打開選單",
            "areas": [
                {
                    "bounds": {
                        "x": 0,
                        "y": 0,
                        "width": 1250,
                        "height": 843
                    },
                    "action": {
                        "type": "uri",
                        "uri": f"https://liff.line.me/{LIFF_ID}"
                    }
                },
                {
                    "bounds": {
                        "x": 1250,
                        "y": 0,
                        "width": 1250,
                        "height": 843
                    },
                    "action": {
                        "type": "uri",
                        "uri": f"https://liff.line.me/{GROUP_LIFF_ID}"
                    }
                },
                {
                    "bounds": {
                        "x": 0,
                        "y": 843,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "!打卡報表"
                    }
                },
                {
                    "bounds": {
                        "x": 833,
                        "y": 843,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "!幫助"
                    }
                },
                {
                    "bounds": {
                        "x": 1666,
                        "y": 843,
                        "width": 834,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "!快速打卡"
                    }
                }
            ]
        }
        
        # 發送請求創建 Rich Menu
        response = requests.post(
            'https://api.line.me/v2/bot/richmenu',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json=rich_menu_data
        )
        
        if response.status_code == 200:
            rich_menu_id = response.json()["richMenuId"]
            print(f"成功創建 Rich Menu: {rich_menu_id}")
            return rich_menu_id
        else:
            print(f"創建 Rich Menu 失敗: {response.text}")
            return None
            
    except Exception as e:
        print(f"創建 Rich Menu 發生錯誤: {e}")
        return None

# 上傳 Rich Menu 圖片
def upload_rich_menu_image(rich_menu_id, image_path):
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        response = requests.post(
            f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers={
                'Content-Type': 'image/jpeg',  # 或 'image/png'
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            data=image_data
        )
        
        if response.status_code == 200:
            print("成功上傳 Rich Menu 圖片")
            return True
        else:
            print(f"上傳 Rich Menu 圖片失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"上傳 Rich Menu 圖片發生錯誤: {e}")
        return False

# 設置為默認 Rich Menu
def set_default_rich_menu(rich_menu_id):
    try:
        response = requests.post(
            f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
            headers={
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            }
        )
        
        if response.status_code == 200:
            print("成功設置默認 Rich Menu")
            return True
        else:
            print(f"設置默認 Rich Menu 失敗: {response.text}")
            return False
            
    except Exception as e:
        print(f"設置默認 Rich Menu 發生錯誤: {e}")
        return False

# 初始化 Rich Menu 的路由
@app.route('/init-rich-menu', methods=['GET'])
def init_rich_menu():
    try:
        # 獲取 Rich Menu 列表
        response = requests.get(
            'https://api.line.me/v2/bot/richmenu/list',
            headers={
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            }
        )
        
        # 刪除現有的 Rich Menu
        if response.status_code == 200:
            rich_menus = response.json().get("richmenus", [])
            for menu in rich_menus:
                requests.delete(
                    f'https://api.line.me/v2/bot/richmenu/{menu["richMenuId"]}',
                    headers={
                        'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
                    }
                )
        
        # 創建新的 Rich Menu
        rich_menu_id = create_rich_menu()
        
        if rich_menu_id:
            # 上傳圖片
            image_uploaded = upload_rich_menu_image(rich_menu_id, 'static/rich_menu.jpg')
            
            if image_uploaded:
                # 設置為默認選單
                if set_default_rich_menu(rich_menu_id):
                    return jsonify({"success": True, "message": "成功創建並設置 Rich Menu"})
        
        return jsonify({"success": False, "message": "設置 Rich Menu 失敗"})
        
    except Exception as e:
        return jsonify({"success": False, "message": f"錯誤: {str(e)}"})

# 自動初始化 Rich Menu (如果需要)
def auto_init_rich_menu():
    try:
        # 獲取 Rich Menu 列表
        response = requests.get(
            'https://api.line.me/v2/bot/richmenu/list',
            headers={
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            }
        )
        
        # 檢查是否需要創建 Rich Menu
        if response.status_code == 200:
            rich_menus = response.json().get("richmenus", [])
            if not rich_menus:  # 如果沒有現有的 Rich Menu
                rich_menu_id = create_rich_menu()
                if rich_menu_id:
                    upload_rich_menu_image(rich_menu_id, 'static/rich_menu.jpg')
                    set_default_rich_menu(rich_menu_id)
    except Exception as e:
        print(f"自動初始化 Rich Menu 錯誤: {e}")

# 健康檢查
@app.route('/')
def index():
    return "打卡系統運行中!"

# 健康檢查/ping 路由
@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({"status": "alive", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}), 200

if __name__ == '__main__':
    # 初始化 Rich Menu
    if os.path.exists('static/rich_menu.jpg'):
        auto_init_rich_menu()
    
    # 啟動保活線程
    start_keep_alive_thread()
    
    # 啟動 Flask 應用
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
