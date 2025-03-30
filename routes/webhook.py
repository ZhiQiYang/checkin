# checkin/routes/webhook.py

from flask import Blueprint, request, jsonify
from datetime import datetime
import json
import requests
from services.notification_service import send_reply, send_checkin_notification, send_line_message_to_group
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
    print(f"==== 收到 webhook 請求 ====")
    
    try:
        data = request.json
        events = data.get('events', [])
        
        for event in events:
            # 先保存可能的群組ID
            if event.get('source', {}).get('type') == 'group':
                recent_group_id = event['source']['groupId']
            
            # 處理文字消息
            if (event.get('type') == 'message' and 
                event.get('message', {}).get('type') == 'text' and 
                event.get('replyToken')):
                
                text = event.get('message', {}).get('text')
                reply_token = event.get('replyToken')
                source_type = event.get('source', {}).get('type')
                
                # 始終發送一個基本回覆
                default_reply = f"收到您的訊息：{text}"
                
                # 根據消息內容執行不同的業務邏輯
                if text.startswith('!'):
                    command = text[1:].lower()
                    print(f"收到命令: {command}")  # 添加日誌
                    
                    # 打卡命令處理
                    if command == '快速打卡' or command == '上班打卡':
                        handle_quick_checkin(event, reply_token, "上班")
                        return 'OK'  # 添加返回，避免繼續執行
                    elif command == '下班打卡':
                        handle_quick_checkin(event, reply_token, "下班")
                    elif command == '打卡報表':
                        # 打卡報表功能
                        report_url = f"{Config.APP_URL}/personal-history?userId={event['source'].get('userId')}"
                        send_reply(reply_token, f"📊 您的打卡報表：\n{report_url}")
                    elif command == '幫助':
                        # 幫助功能
                        help_text = (
                            "📱 打卡系統指令說明：\n"
                            "!上班打卡 - 快速完成上班打卡\n"
                            "!下班打卡 - 快速完成下班打卡\n"
                            "!快速打卡 - 快速完成上班打卡（等同於!上班打卡）\n"
                            "!打卡報表 - 查看打卡統計報表\n"
                            "打卡 - 獲取打卡頁面連結\n"
                            "其他問題請聯繫管理員"
                        )
                        send_reply(reply_token, help_text)
                    else:
                        # 其他命令使用默認回覆
                        send_reply(reply_token, default_reply)
                elif text in ['打卡', '打卡連結']:
                    liff_url = f"https://liff.line.me/{Config.LIFF_ID}"
                    send_reply(reply_token, f"請點擊以下連結進行打卡：\n{liff_url}")
                else:
                    # 不符合特殊條件的消息使用默認回覆
                    send_reply(reply_token, default_reply)
                
                # 處理群組消息存儲
                if source_type == 'group' and event['source']['groupId'] == Config.LINE_GROUP_ID:
                    user_id = event['source'].get('userId')
                    if user_id:
                        # 獲取用戶資料並保存群組消息
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
        
        return 'OK'
    except Exception as e:
        error_msg = f"處理 webhook 時出錯: {str(e)}"
        print(error_msg)
        return 'OK'

@webhook_bp.route('/webhook-response-test', methods=['POST'])
def webhook_response_test():
    body = request.get_data(as_text=True)
    print(f"==== 收到 webhook-response-test 請求 ====")
    print(f"請求內容: {body}")
    
    result = {
        "received": True,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "events": []
    }
    
    try:
        data = request.json
        events = data.get('events', [])
        
        for event in events:
            event_info = {
                "type": event.get('type'),
                "source_type": event.get('source', {}).get('type'),
                "reply_token": event.get('replyToken')
            }
            
            # 如果是文字消息，嘗試直接回覆
            if (event.get('type') == 'message' and 
                event.get('message', {}).get('type') == 'text' and 
                event.get('replyToken')):
                
                reply_text = f"收到您的訊息：{event.get('message', {}).get('text')}"
                try:
                    # 嘗試回覆
                    send_reply(event.get('replyToken'), reply_text)
                    event_info["reply_sent"] = True
                except Exception as e:
                    event_info["reply_sent"] = False
                    event_info["reply_error"] = str(e)
            
            result["events"].append(event_info)
        
        # 同時嘗試發送群組消息
        try:
            group_msg = f"測試群組訊息 - {datetime.now().strftime('%H:%M:%S')}"
            group_sent = send_line_message_to_group(group_msg)
            result["group_message_sent"] = group_sent
        except Exception as e:
            result["group_message_sent"] = False
            result["group_message_error"] = str(e)
        
        return jsonify(result)
    except Exception as e:
        result["error"] = str(e)
        return jsonify(result)

@webhook_bp.route('/webhook-detailed', methods=['POST'])
def webhook_detailed():
    body = request.get_data(as_text=True)
    print(f"==== 收到 webhook-detailed 請求 ====")
    
    response_data = {
        "received": True,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "body_length": len(body),
        "events_count": 0,
        "events_details": []
    }
    
    try:
        data = request.json
        events = data.get('events', [])
        response_data["events_count"] = len(events)
        
        for event in events:
            event_details = {
                "type": event.get('type'),
                "source_type": event.get('source', {}).get('type'),
                "has_reply_token": bool(event.get('replyToken')),
                "message_type": event.get('message', {}).get('type') if event.get('type') == 'message' else None,
                "text": event.get('message', {}).get('text') if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text' else None
            }
            response_data["events_details"].append(event_details)
            
        return jsonify(response_data)
    except Exception as e:
        response_data["error"] = str(e)
        return jsonify(response_data)

@webhook_bp.route('/app-debug', methods=['GET'])
def app_debug():
    import sqlite3
    
    # 收集應用狀態信息
    status = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "app_running": True,
        "db_path": Config.DB_PATH
    }
    
    # 測試數據庫連接和查詢
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        
        # 檢查打卡記錄
        c.execute("SELECT COUNT(*) FROM checkin_records")
        status["checkin_count"] = c.fetchone()[0]
        
        # 檢查最近打卡
        c.execute("SELECT * FROM checkin_records ORDER BY id DESC LIMIT 1")
        last_record = c.fetchone()
        if last_record:
            status["last_checkin"] = dict(zip([col[0] for col in c.description], last_record))
        
        # 檢查群組消息
        c.execute("SELECT COUNT(*) FROM group_messages")
        status["messages_count"] = c.fetchone()[0]
        
        conn.close()
        status["db_connection"] = "OK"
    except Exception as e:
        status["db_connection"] = "ERROR"
        status["db_error"] = str(e)
    
    return jsonify(status)

@webhook_bp.route('/test-file-system', methods=['GET'])
def test_file_system():
    try:
        # 測試寫入
        test_file = "test_file.json"
        test_data = {"test": "data", "timestamp": str(datetime.now())}
        
        with open(test_file, 'w') as f:
            json.dump(test_data, f)
        
        # 測試讀取
        with open(test_file, 'r') as f:
            read_data = json.load(f)
        
        # 測試讀取已有檔案
        existing_files = []
        try:
            with open("checkin_records.json", 'r') as f:
                existing_files.append({"file": "checkin_records.json", "exists": True})
        except Exception as e:
            existing_files.append({"file": "checkin_records.json", "exists": False, "error": str(e)})
            
        try:
            with open("group_messages.json", 'r') as f:
                existing_files.append({"file": "group_messages.json", "exists": True})
        except Exception as e:
            existing_files.append({"file": "group_messages.json", "exists": False, "error": str(e)})
        
        return {
            "success": True,
            "write_test": "成功",
            "read_test": read_data,
            "existing_files": existing_files
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "detail": repr(e)
        }

@webhook_bp.route('/debug-send', methods=['GET'])
def debug_send():
    try:
        # 測試發送訊息到群組
        message = "🔍 測試訊息 - 來自調試功能"
        success = send_line_message_to_group(message)
        
        # 返回結果
        return jsonify({
            "success": success,
            "message": "訊息發送成功" if success else "訊息發送失敗",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({"error": str(e)})

@webhook_bp.route('/view-logs', methods=['GET'])
def view_logs():
    try:
        with open('webhook_logs.txt', 'r', encoding='utf-8') as f:
            logs = f.read()
        return f"<pre>{logs}</pre>"
    except Exception as e:
        return f"讀取日誌檔案失敗: {str(e)}"

@webhook_bp.route('/webhook-test', methods=['POST'])
def webhook_test():
    print("正在處理 webhook 測試請求")
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

@webhook_bp.route('/webhook-debug', methods=['GET', 'POST'])
def webhook_debug():
    if request.method == 'POST':
        body = request.get_data(as_text=True)
        return f"收到 POST 請求: {body[:100]}..."
    else:
        return "webhook 調試端點正常運行"

@webhook_bp.route('/test-message-api', methods=['GET'])
def test_message_api():
    try:
        result = send_line_message_to_group("這是一條測試訊息")
        return {
            "success": result,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": "測試發送結果"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "detail": repr(e)
        }

@webhook_bp.route('/send-test-message', methods=['GET'])
def send_test_message():
    try:
        # 嘗試直接發送消息到群組
        message = f"測試消息 - {datetime.now().strftime('%H:%M:%S')}"
        success = send_line_message_to_group(message)
        
        return jsonify({
            "success": success,
            "message": "訊息已發送" if success else "發送失敗",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        return jsonify({"error": str(e)})

# 更新 routes/webhook.py 中的 handle_quick_checkin 函數
def handle_quick_checkin(event, reply_token, checkin_type="上班"):
    try:
        print(f"執行快速打卡: {checkin_type}")
        user_id = event['source'].get('userId')
        if not user_id:
            send_reply(reply_token, "無法獲取用戶信息，請使用 LIFF 頁面打卡")
            return

        # 使用靜態用戶名進行測試
        display_name = "用戶" 
        try:
            profile_response = requests.get(
                f'https://api.line.me/v2/bot/profile/{user_id}',
                headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
            )
            if profile_response.status_code == 200:
                profile = profile_response.json()
                display_name = profile.get('displayName', '未知用戶')
        except Exception as e:
            print(f"獲取用戶資料錯誤: {e}")

        # 直接執行打卡
        success, message, timestamp = quick_checkin(user_id, display_name, checkin_type)
        
        if success:
            send_reply(reply_token, f"✅ {message}")
        else:
            send_reply(reply_token, f"❌ {message}")
            
    except Exception as e:
        print(f"快速打卡處理錯誤: {str(e)}")
        send_reply(reply_token, "處理打卡請求時出錯，請稍後再試")

# 在 routes/webhook.py 中添加一個測試端點
@webhook_bp.route('/test-quick-checkin/<user_id>/<name>/<checkin_type>', methods=['GET'])
def test_quick_checkin(user_id, name, checkin_type="上班"):
    """測試快速打卡的端點"""
    success, message, timestamp = quick_checkin(user_id, name, checkin_type)
    
    result = {
        "success": success,
        "message": message,
        "timestamp": timestamp,
        "note": f"通過指令快速{checkin_type}打卡"
    }
    
    # 如果成功，也發送群組通知
    if success:
        notification = f"✅ {name} 已於 {timestamp} 完成{checkin_type}打卡\n📝 備註: 透過指令快速{checkin_type}打卡"
        sent = send_line_message_to_group(notification)
        result["notification_sent"] = sent
    
    return jsonify(result)

# 添加到 routes/webhook.py
@webhook_bp.route('/fix-database', methods=['GET'])
def fix_database():
    try:
        from db.update_db import update_database
        result = update_database()
        
        # 創建測試記錄
        from services.checkin_service import process_checkin
        user_id = request.args.get('userId', 'test_user')
        success, message, timestamp = process_checkin(
            user_id, 
            "測試用戶", 
            "系統測試", 
            note="數據庫修復測試", 
            checkin_type="上班"
        )
        
        return jsonify({
            "db_update": "完成",
            "test_record": {
                "success": success,
                "message": message,
                "timestamp": timestamp
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)})
