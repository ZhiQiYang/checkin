# routes/api.py

from flask import Blueprint, request, jsonify
from services.checkin_service import process_checkin as process_checkin_logic
from services.group_service import save_group_message, get_recent_messages
from services.notification_service import send_line_message_to_group, send_line_notification
from datetime import datetime
from utils.validator import validate_checkin_input
from db.crud import get_reminder_setting, update_reminder_setting

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/checkin', methods=['POST'])
def handle_checkin():
    try:
        data = request.json
        
        # 調試信息
        print(f"收到打卡請求: {data}")
        
        # 驗證輸入
        errors = validate_checkin_input(data)
        if errors:
            return jsonify({'success': False, 'message': ', '.join(errors)}), 400
        
        user_id = data.get('userId')
        display_name = data.get('displayName')
        location = data.get('location', '未提供位置')
        note = data.get('note')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        checkin_type = data.get('checkinType', '上班')  # 默認上班打卡

        success, message, timestamp = process_checkin_logic(
            user_id, display_name, location,
            note=note, latitude=latitude, longitude=longitude, 
            checkin_type=checkin_type
        )

        if success:
            notification = f"✅ {display_name} 已於 {timestamp} 完成{checkin_type}打卡\n📍 位置: {location}"
            if note:
                notification += f"\n📝 備註: {note}"
            if latitude and longitude:
                notification += f"\n🗺️ https://www.google.com/maps?q={latitude},{longitude}"

            if not send_line_message_to_group(notification):
                message += "（通知發送失敗）"

        return jsonify({'success': success, 'message': message})
    except Exception as e:
        print(f"處理打卡API請求時出錯: {str(e)}")
        return jsonify({'success': False, 'message': f'系統錯誤: {str(e)}'}), 500

# 提醒設置 API
@api_bp.route('/api/reminder/settings', methods=['GET'])
def get_reminder_settings():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'success': False, 'message': '缺少用戶ID'}), 400
    
    settings = get_reminder_setting(user_id)
    return jsonify({
        'success': True,
        'settings': settings
    })

@api_bp.route('/api/reminder/settings', methods=['POST'])
def update_reminder_settings():
    data = request.json
    user_id = data.get('userId')
    
    if not user_id:
        return jsonify({'success': False, 'message': '缺少用戶ID'}), 400
    
    success = update_reminder_setting(user_id, data)
    return jsonify({
        'success': success,
        'message': '設置已更新' if success else '更新設置失敗'
    })

@api_bp.route('/api/reminder/test', methods=['POST'])
def test_reminder():
    """測試發送提醒"""
    data = request.json
    user_id = data.get('userId')
    name = data.get('name', '用戶')
    reminder_type = data.get('type', 'morning')
    
    if not user_id:
        return jsonify({'success': False, 'message': '缺少用戶ID'}), 400
    
    if reminder_type == 'morning':
        message = f"⏰ 測試 - {name}，早安！您今天還沒有上班打卡，請記得打卡。"
    else:
        message = f"⏰ 測試 - {name}，下班時間到了！您今天還沒有下班打卡，請記得打卡。"
    
    success = send_line_notification(user_id, message)
    
    return jsonify({
        'success': success,
        'message': '測試提醒已發送' if success else '發送測試提醒失敗'
    })
