from flask import Blueprint, request, jsonify
from services.checkin_service import process_checkin as process_checkin_logic
from services.group_service import save_group_message, get_recent_messages
from services.notification_service import send_line_message_to_group
from datetime import datetime
from utils.validator import validate_checkin_input

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/checkin', methods=['POST'])
def handle_checkin():
    data = request.json
    
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

    success, message, timestamp = process_checkin_logic(
        user_id, display_name, location,
        note=note, latitude=latitude, longitude=longitude
    )

    if success:
        notification = f"✅ {display_name} 已於 {timestamp} 完成打卡\n📍 位置: {location}"
        if note:
            notification += f"\n📝 備註: {note}"
        if latitude and longitude:
            notification += f"\n🗺️ https://www.google.com/maps?q={latitude},{longitude}"

        if not send_line_message_to_group(notification):
            message += "（通知發送失敗）"

    return jsonify({'success': success, 'message': message})
