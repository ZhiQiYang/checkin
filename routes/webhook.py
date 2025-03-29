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

def webhook():
    global recent_group_id
    body = request.get_data(as_text=True)
    print(f"==== 收到 webhook 請求 ====")
    print(f"請求內容: {body}")
    
    # 寫入日誌文件
    with open('webhook_logs.txt', 'a', encoding='utf-8') as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 收到請求: {body}\n")
    
    try:
        # 嘗試直接回覆一條測試消息
        if "events" in body and "replyToken" in body:
            events = request.json.get('events', [])
            for event in events:
                if "replyToken" in event:
                    reply_token = event.get('replyToken')
                    send_reply(reply_token, "收到請求，正在處理...")
                    print(f"嘗試回覆 token: {reply_token}")
        
        # 原有邏輯
        # ... 原有代碼 ...
    except Exception as e:
        error_msg = f"處理 webhook 時出錯: {str(e)}"
        print(error_msg)
        with open('webhook_logs.txt', 'a', encoding='utf-8') as f:
            f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 錯誤: {error_msg}\n")
    
    return 'OK'

@webhook_bp.route('/webhook-test', methods=['POST'])
def webhook_test():  # 這裡改為 webhook_test 而不是 webhook
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


@webhook_bp.route('/webhook-debug', methods=['GET', 'POST'])
def webhook_debug():
    if request.method == 'POST':
        body = request.get_data(as_text=True)
        return f"收到 POST 請求: {body[:100]}..."
    else:
        return "webhook 調試端點正常運行"


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
