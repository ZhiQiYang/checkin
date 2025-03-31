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

            # 新增查詢ID功能
            if (event.get('type') == 'message' and 
                event.get('message', {}).get('type') == 'text' and 
                event.get('replyToken') and
                event.get('source', {}).get('userId')):    
                text = event.get('message', {}).get('text')
                reply_token = event.get('replyToken')
                user_id = event['source'].get('userId')
    
                # 顯示用戶 ID 在伺服器日誌
                print(f"用戶 ID: {user_id}")
                
                # 如果消息內容是 "查詢ID"，回覆用戶 ID
                if text == "查詢ID":
                    send_reply(reply_token, f"您的用戶 ID 是: {user_id}")
                    return 'OK'  # 處理完畢，跳過其他邏輯
            
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
                        return 'OK'
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
                            "!測試提醒 - 發送測試提醒\n"
                            "!系統狀態 - 查看系統運行狀態\n"
                            "!管理指令 - 顯示管理員指令列表\n"
                            "打卡 - 獲取打卡頁面連結\n"
                            "其他問題請聯繫管理員"
                        )
                        send_reply(reply_token, help_text)
                    elif command == '測試提醒':
                        # 測試發送提醒
                        user_id = event['source'].get('userId')
                        if user_id:
                            # 獲取用戶資料
                            try:
                                profile_response = requests.get(
                                    f'https://api.line.me/v2/bot/profile/{user_id}',
                                    headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
                                )
                                
                                if profile_response.status_code == 200:
                                    profile = profile_response.json()
                                    display_name = profile.get('displayName', '用戶')
                                    
                                    # 發送測試提醒
                                    from services.notification_service import send_line_notification
                                    message = f"⏰ 測試 - {display_name}，早安！您今天還沒有上班打卡，請記得打卡。"
                                    send_line_notification(user_id, message)
                                    
                                    send_reply(reply_token, "✅ 測試提醒已發送，請查看您的LINE通知")
                                else:
                                    send_reply(reply_token, "❌ 無法獲取用戶資料，請稍後再試")
                            except Exception as e:
                                send_reply(reply_token, f"❌ 發送提醒時出錯: {str(e)[:30]}...")
                        else:
                            send_reply(reply_token, "❌ 無法獲取用戶ID，請稍後再試")
                    elif command == '系統狀態':
                        # 查詢系統狀態
                        try:
                            import sqlite3
                            from datetime import datetime
                            
                            status_text = f"📊 系統狀態報告 ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})\n"
                            
                            # 檢查數據庫
                            conn = sqlite3.connect(Config.DB_PATH)
                            c = conn.cursor()
                            
                            # 檢查打卡記錄數
                            c.execute("SELECT COUNT(*) FROM checkin_records")
                            checkin_count = c.fetchone()[0]
                            status_text += f"✓ 打卡記錄總數: {checkin_count} 筆\n"
                            
                            # 檢查今日打卡數
                            today = datetime.now().strftime("%Y-%m-%d")
                            c.execute("SELECT COUNT(*) FROM checkin_records WHERE date = ?", (today,))
                            today_count = c.fetchone()[0]
                            status_text += f"✓ 今日打卡數: {today_count} 筆\n"
                            
                            # 檢查用戶數
                            c.execute("SELECT COUNT(*) FROM users")
                            user_count = c.fetchone()[0]
                            status_text += f"✓ 用戶總數: {user_count} 人\n"
                            
                            # 檢查最近一次打卡
                            c.execute("SELECT name, date, time, checkin_type FROM checkin_records ORDER BY id DESC LIMIT 1")
                            last_record = c.fetchone()
                            if last_record:
                                status_text += f"✓ 最近打卡: {last_record[0]} 於 {last_record[1]} {last_record[2]} {last_record[3]}打卡\n"
                            
                            conn.close()
                            
                            # 添加系統版本信息
                            status_text += f"✓ 系統運行正常\n✓ 版本: 2025.04.01"
                            
                            send_reply(reply_token, status_text)
                        except Exception as e:
                            send_reply(reply_token, f"❌ 獲取系統狀態時出錯: {str(e)[:30]}...")
                    elif command == '管理指令':
                        # 檢查是否為管理員
                        user_id = event['source'].get('userId')
                        from routes.admin import ADMIN_IDS  # 導入管理員列表
                        
                        if user_id in ADMIN_IDS:
                            admin_help = (
                                "🔧 管理員指令列表：\n"
                                "!重置菜單 - 重置LINE Rich Menu\n"
                                "!診斷系統 - 執行系統診斷\n"
                                "!備份數據 - 觸發數據庫備份\n"
                                "!清理緩存 - 清理系統緩存\n"
                                "!發送群通知 - 發送全群通知\n"
                            )
                            send_reply(reply_token, admin_help)
                        else:
                            send_reply(reply_token, "⚠️ 您不是管理員，無法查看管理指令")
                    elif command == '重置菜單' and event['source'].get('userId') in ADMIN_IDS:
                        # 重置Rich Menu (僅管理員)
                        from services.rich_menu_service import init_rich_menu_process
                        success, message = init_rich_menu_process()
                        send_reply(reply_token, f"{'✅' if success else '❌'} {message}")
                    elif command == '診斷系統' and event['source'].get('userId') in ADMIN_IDS:
                        # 執行系統診斷 (僅管理員)
                        send_reply(reply_token, "🔍 系統診斷已啟動，報告將稍後發送")
                        
                        # 異步執行診斷
                        import threading
                        def run_diagnostic():
                            try:
                                import requests
                                diagnostic_response = requests.get(f"{Config.APP_URL}/system-diagnostic")
                                if diagnostic_response.status_code == 200:
                                    from services.notification_service import send_line_notification
                                    send_line_notification(event['source'].get('userId'), "📊 系統診斷完成，請訪問管理面板查看詳細報告")
                            except Exception as e:
                                print(f"診斷錯誤: {e}")
                        
                        thread = threading.Thread(target=run_diagnostic)
                        thread.daemon = True
                        thread.start()
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

# ... (以下其他函數保持不變，請參考上面的完整代碼)

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
        import os
        # 檢查日誌文件是否存在
        log_files = []
        if os.path.exists('logs'):
            log_files = [f for f in os.listdir('logs') if f.endswith('.log')]
        
        # 查找可能的日誌文件
        possible_logs = ['logs/app.log', 'app.log', 'error.log']
        log_content = "找不到日誌文件"
        
        # 嘗試讀取日誌文件
        for log_file in possible_logs + ['logs/' + f for f in log_files]:
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    # 讀取最後1000行
                    lines = f.readlines()[-1000:]
                    log_content = ''.join(lines)
                break
        
        return f"<pre>{log_content}</pre>"
    except Exception as e:
        return f"讀取日誌失敗: {str(e)}"

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

def handle_quick_checkin(event, reply_token, checkin_type="上班"):
    try:
        print(f"執行快速打卡: {checkin_type}")
        user_id = event['source'].get('userId')
        if not user_id:
            send_reply(reply_token, "無法獲取用戶信息，請使用 LIFF 頁面打卡")
            return
            
        # 使用靜態用戶名進行測試
        display_name = "用戶" 
        
        # 獲取用戶資料 - 添加詳細日誌
        try:
            print(f"嘗試獲取用戶資料: {user_id}")
            profile_response = requests.get(
                f'https://api.line.me/v2/bot/profile/{user_id}',
                headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
            )
            print(f"獲取用戶資料響應狀態: {profile_response.status_code}")
            
            if profile_response.status_code == 200:
                profile = profile_response.json()
                display_name = profile.get('displayName', '未知用戶')
                print(f"獲取到用戶名稱: {display_name}")
            else:
                print(f"獲取用戶資料失敗: {profile_response.text}")
        except Exception as e:
            print(f"獲取用戶資料錯誤詳情: {str(e)}")
            import traceback
            print(traceback.format_exc())
        
        # 執行打卡前記錄
        print(f"準備執行打卡: 用戶={user_id}, 名稱={display_name}, 類型={checkin_type}")
        
        # 直接執行打卡
        try:
            success, message, timestamp = quick_checkin(user_id, display_name, checkin_type)
            print(f"打卡結果: success={success}, message={message}, time={timestamp}")
        except Exception as e:
            print(f"quick_checkin 函數錯誤: {str(e)}")
            import traceback
            print(traceback.format_exc())
            raise  # 重新拋出異常以便外層捕獲
        
        if success:
            try:
                # 嘗試發送通知
                notification = f"✅ {display_name} 已於 {timestamp} 完成{checkin_type}打卡\n📝 備註: 透過指令快速{checkin_type}打卡"
                notification_sent = send_checkin_notification(display_name, timestamp, f"快速{checkin_type}打卡", 
                                     note=f"透過指令快速{checkin_type}打卡")
                print(f"通知發送結果: {notification_sent}")
            except Exception as e:
                print(f"發送通知錯誤: {str(e)}")
            
            send_reply(reply_token, f"✅ {message}")
        else:
            send_reply(reply_token, f"❌ {message}")
            
    except Exception as e:
        print(f"快速打卡處理錯誤: {str(e)}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"錯誤詳情:\n{error_trace}")
        
        # 返回更詳細的錯誤信息
        send_reply(reply_token, f"處理打卡請求時出錯: {str(e)[:30]}...")

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

@webhook_bp.route('/diagnose-quick-checkin', methods=['GET'])
def diagnose_quick_checkin():
    from services.checkin_service import quick_checkin
    
    try:
        # 獲取參數
        user_id = request.args.get('userId', 'test_user_id')
        name = request.args.get('name', '測試用戶')
        checkin_type = request.args.get('type', '上班')
        
        # 收集診斷信息
        diagnostics = {
            "配置檢查": {
                "LINE_GROUP_ID": Config.LINE_GROUP_ID,
                "LINE_ACCESS_TOKEN": Config.MESSAGING_CHANNEL_ACCESS_TOKEN[:10] + "..." if Config.MESSAGING_CHANNEL_ACCESS_TOKEN else None,
                "APP_URL": Config.APP_URL
            },
            "數據庫檢查": {}
        }
        
        # 檢查數據庫
        import sqlite3
        try:
            conn = sqlite3.connect('checkin.db')
            cursor = conn.cursor()
            
            # 檢查表結構
            cursor.execute("PRAGMA table_info(checkin_records)")
            columns = cursor.fetchall()
            diagnostics["數據庫檢查"]["表結構"] = columns
            
            # 檢查記錄數
            cursor.execute("SELECT COUNT(*) FROM checkin_records")
            count = cursor.fetchone()[0]
            diagnostics["數據庫檢查"]["記錄數"] = count
            
            conn.close()
        except Exception as e:
            diagnostics["數據庫檢查"]["錯誤"] = str(e)
        
        # 嘗試執行快速打卡
        result = {
            "準備執行": f"用戶ID: {user_id}, 名稱: {name}, 類型: {checkin_type}"
        }
        
        try:
            success, message, timestamp = quick_checkin(user_id, name, checkin_type)
            result["執行結果"] = {
                "success": success,
                "message": message,
                "timestamp": timestamp
            }
        except Exception as e:
            import traceback
            result["執行錯誤"] = {
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        
        # 返回診斷結果
        return jsonify({
            "診斷時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "診斷資訊": diagnostics,
            "快速打卡執行": result
        })
    except Exception as e:
        return jsonify({"診斷錯誤": str(e)})

@webhook_bp.route('/system-diagnostic', methods=['GET'])
def system_diagnostic():
    import os
    import sqlite3
    import json
    import requests
    from datetime import datetime
    from config import Config
    
    diagnostic = {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "系統狀態": "運行中",
        "測試項目": {}
    }
    
    # 1. 檢查配置
    try:
        diagnostic["配置"] = {
            "LINE_LOGIN_CHANNEL_ID": Config.LINE_LOGIN_CHANNEL_ID is not None,
            "LINE_LOGIN_CHANNEL_SECRET": Config.LINE_LOGIN_CHANNEL_SECRET is not None,
            "MESSAGING_CHANNEL_ACCESS_TOKEN": Config.MESSAGING_CHANNEL_ACCESS_TOKEN is not None,
            "LINE_GROUP_ID": Config.LINE_GROUP_ID is not None,
            "LIFF_ID": Config.LIFF_ID is not None,
            "APP_URL": Config.APP_URL
        }
    except Exception as e:
        diagnostic["配置"] = {"錯誤": str(e)}
    
    # 2. 檢查數據庫
    try:
        if os.path.exists(Config.DB_PATH):
            diagnostic["數據庫"] = {
                "文件存在": True,
                "文件大小": f"{os.path.getsize(Config.DB_PATH)} 字節"
            }
            
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            
            # 檢查表結構
            table_structure = {}
            for table in ["checkin_records", "group_messages"]:
                c.execute(f"PRAGMA table_info({table})")
                columns = c.fetchall()
                table_structure[table] = [col[1] for col in columns]
            
            diagnostic["數據庫"]["表結構"] = table_structure
            
            # 檢查記錄數
            c.execute("SELECT COUNT(*) FROM checkin_records")
            diagnostic["數據庫"]["打卡記錄數"] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM group_messages")
            diagnostic["數據庫"]["群組消息數"] = c.fetchone()[0]
            
            conn.close()
        else:
            diagnostic["數據庫"] = {
                "文件存在": False,
                "解決方案": "需要初始化數據庫"
            }
    except Exception as e:
        diagnostic["數據庫"] = {"錯誤": str(e)}
    
    # 3. 測試 LINE API
    try:
        headers = {
            'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
        }
        
        # 測試 Bot 信息
        bot_response = requests.get('https://api.line.me/v2/bot/info', headers=headers)
        
        diagnostic["LINE API"] = {
            "狀態碼": bot_response.status_code,
            "有效性": bot_response.status_code == 200
        }
        
        if bot_response.status_code == 200:
            diagnostic["LINE API"]["Bot信息"] = bot_response.json()
        else:
            diagnostic["LINE API"]["錯誤"] = bot_response.text
    except Exception as e:
        diagnostic["LINE API"] = {"錯誤": str(e)}
    
    # 4. 測試打卡功能
    try:
        from services.checkin_service import process_checkin
        
        success, message, timestamp = process_checkin(
            "test_diagnostic", 
            "診斷測試", 
            "系統診斷", 
            note="自動診斷測試", 
            checkin_type="上班"
        )
        
        diagnostic["測試項目"]["基本打卡"] = {
            "成功": success,
            "消息": message,
            "時間": timestamp
        }
    except Exception as e:
        import traceback
        diagnostic["測試項目"]["基本打卡"] = {
            "錯誤": str(e),
            "詳細信息": traceback.format_exc()
        }
    
    # 5. 測試 quick_checkin 功能
    try:
        from services.checkin_service import quick_checkin
        
        success, message, timestamp = quick_checkin(
            "test_diagnostic", 
            "診斷測試", 
            "上班"
        )
        
        diagnostic["測試項目"]["快速打卡"] = {
            "成功": success,
            "消息": message,
            "時間": timestamp
        }
    except Exception as e:
        import traceback
        diagnostic["測試項目"]["快速打卡"] = {
            "錯誤": str(e),
            "詳細信息": traceback.format_exc()
        }
    
    # 6. 測試發送群組消息
    try:
        from services.notification_service import send_line_message_to_group
        
        message = f"📱 系統診斷測試 - {datetime.now().strftime('%H:%M:%S')}"
        result = send_line_message_to_group(message)
        
        diagnostic["測試項目"]["群組消息"] = {
            "成功": result,
            "目標群組": Config.LINE_GROUP_ID
        }
    except Exception as e:
        diagnostic["測試項目"]["群組消息"] = {"錯誤": str(e)}
    
    # 返回診斷結果
    return jsonify(diagnostic)

@webhook_bp.route('/emergency-reset', methods=['GET'])
def emergency_reset():
    import os
    import sqlite3
    from config import Config
    from datetime import datetime
    
    result = {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "操作": "緊急重置"
    }
    
    # 重建數據庫
    try:
        # 備份現有數據庫
        if os.path.exists(Config.DB_PATH):
            backup_path = f"{Config.DB_PATH}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            os.rename(Config.DB_PATH, backup_path)
            result["備份"] = f"數據庫已備份為 {backup_path}"
        
        # 創建新數據庫
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        
        # 建立打卡紀錄表格
        c.execute('''
            CREATE TABLE checkin_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                name TEXT NOT NULL,
                location TEXT,
                note TEXT,
                latitude REAL,
                longitude REAL,
                date TEXT NOT NULL,
                time TEXT NOT NULL,
                checkin_type TEXT DEFAULT '上班'
            )
        ''')
        
        # 建立群組訊息表格
        c.execute('''
            CREATE TABLE group_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                user_name TEXT NOT NULL,
                message TEXT,
                timestamp TEXT NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        
        result["數據庫"] = "重建成功"
        
        # 創建測試記錄
        try:
            from services.checkin_service import process_checkin
            
            success, message, timestamp = process_checkin(
                "emergency_reset", 
                "系統重置", 
                "緊急重置", 
                note="系統緊急重置測試", 
                checkin_type="上班"
            )
            
            result["測試記錄"] = {
                "成功": success,
                "消息": message,
                "時間": timestamp
            }
        except Exception as e:
            result["測試記錄"] = {"錯誤": str(e)}
        
    except Exception as e:
        result["錯誤"] = str(e)
    
    return jsonify(result)

@webhook_bp.route('/function-test', methods=['GET'])
def function_test():
    function_name = request.args.get('function', 'quick_checkin')
    user_id = request.args.get('userId', 'test_user')
    
    result = {
        "函數": function_name,
        "參數": {
            "user_id": user_id,
            "其他參數": "根據函數類型自動設置"
        }
    }
    
    try:
        if function_name == 'quick_checkin':
            from services.checkin_service import quick_checkin
            success, message, timestamp = quick_checkin(user_id, "測試用戶", "上班")
            result["結果"] = {
                "success": success,
                "message": message,
                "timestamp": timestamp
            }
        
        elif function_name == 'save_checkin':
            from db.crud import save_checkin
            success, message = save_checkin(user_id, "測試用戶", "測試位置", "測試備註", None, None, "上班")
            result["結果"] = {
                "success": success,
                "message": message
            }
        
        elif function_name == 'send_message':
            from services.notification_service import send_line_message_to_group
            success = send_line_message_to_group("這是一條測試消息")
            result["結果"] = {
                "success": success
            }
        
        else:
            result["錯誤"] = f"未知函數: {function_name}"
    
    except Exception as e:
        import traceback
        result["錯誤"] = {
            "message": str(e),
            "traceback": traceback.format_exc()
        }
    
    return jsonify(result)

@webhook_bp.route('/emergency-db-fix', methods=['GET'])
def emergency_db_fix():
    import sqlite3
    from config import Config
    from datetime import datetime
    import os
    
    result = {
        "時間": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "操作": "數據庫緊急修復"
    }
    
    try:
        # 檢查數據庫是否存在
        if os.path.exists(Config.DB_PATH):
            # 備份數據庫
            backup_path = f"{Config.DB_PATH}.bak.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            import shutil
            shutil.copy2(Config.DB_PATH, backup_path)
            result["備份"] = f"數據庫已備份為 {backup_path}"
            
            # 連接數據庫
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            
            # 檢查表結構
            c.execute("PRAGMA table_info(checkin_records)")
            columns = c.fetchall()
            column_names = [col[1] for col in columns]
            result["現有欄位"] = column_names
            
            # 檢查是否有 checkin_type 欄位
            if "checkin_type" not in column_names:
                # 添加 checkin_type 欄位
                try:
                    c.execute("ALTER TABLE checkin_records ADD COLUMN checkin_type TEXT DEFAULT '上班'")
                    conn.commit()
                    result["修改"] = "成功添加 checkin_type 欄位"
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        result["修改"] = "欄位已存在，無需添加"
                    else:
                        raise
            else:
                result["修改"] = "欄位已存在，無需添加"
            
            # 驗證修改
            c.execute("PRAGMA table_info(checkin_records)")
            updated_columns = c.fetchall()
            result["更新後欄位"] = [col[1] for col in updated_columns]
            
            # 關閉連接
            conn.close()
        else:
            # 創建新數據庫
            result["狀態"] = "數據庫不存在，創建新數據庫"
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            
            # 建立打卡紀錄表格
            c.execute('''
                CREATE TABLE checkin_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    location TEXT,
                    note TEXT,
                    latitude REAL,
                    longitude REAL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    checkin_type TEXT DEFAULT '上班'
                )
            ''')
            
            # 建立群組訊息表格
            c.execute('''
                CREATE TABLE group_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    message TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')
            
            conn.commit()
            conn.close()
            result["創建"] = "數據庫和表格創建成功"
        
        # 測試記錄
        try:
            from services.checkin_service import process_checkin
            success, message, timestamp = process_checkin(
                "emergency_fix", 
                "系統修復", 
                "緊急修復", 
                note="系統緊急修復測試", 
                checkin_type="上班"
            )
            
            result["測試記錄"] = {
                "成功": success,
                "消息": message,
                "時間": timestamp
            }
        except Exception as e:
            result["測試記錄"] = {"錯誤": str(e)}
        
    except Exception as e:
        import traceback
        result["錯誤"] = str(e)
        result["詳細錯誤"] = traceback.format_exc()
    
    return jsonify(result)

