from flask import Blueprint, request, jsonify
from datetime import datetime
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
    print(f"請求內容: {body}")
    
    # 寫入日誌文件
    try:
        with open('webhook_logs.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 收到請求: {body}\n")
    except Exception as e:
        print(f"寫入日誌文件失敗: {e}")
    
    try:
        events = request.json.get('events', [])
        print(f"解析到 {len(events)} 個事件")
        
        for event in events:
            if event.get('source', {}).get('type') == 'group':
                recent_group_id = event['source']['groupId']

            if event.get('type') == 'message' and event.get('message', {}).get('type') == 'text':
                text = event.get('message', {}).get('text')
                reply_token = event.get('replyToken')
                source_type = event.get('source', {}).get('type')
                
                print(f"收到文字訊息: {text}, 回覆令牌: {reply_token}")

                if text.startswith('!'):
                    command = text[1:].lower()
                    print(f"檢測到指令: {command}")

                    if command == '快速打卡':
                        print("處理快速打卡指令")
                        handle_quick_checkin(event, reply_token)
                        print("快速打卡處理完成")

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
        error_msg = f"處理 webhook 時出錯: {str(e)}"
        print(error_msg)
        try:
            with open('webhook_logs.txt', 'a', encoding='utf-8') as f:
                f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 錯誤: {error_msg}\n")
        except:
            pass
    
    return 'OK'

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
