from flask import Blueprint, request, jsonify
from services.checkin_service import process_checkin
from services.group_service import save_group_message, get_recent_messages
from services.notification_service import send_line_message_to_group
from datetime import datetime

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/checkin', methods=['POST'])
def process_checkin():
    data = request.json
    user_id = data.get('userId')
    display_name = data.get('displayName')
    location = data.get('location', '未提供位置')
    note = data.get('note')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success, message, timestamp = process_checkin(
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


@api_bp.route('/api/group/messages', methods=['GET'])
def get_messages():
    count = int(request.args.get('count', 20))
    messages = get_recent_messages(count)
    return jsonify({'success': True, 'messages': messages})


@api_bp.route('/api/group/send', methods=['POST'])
def send_message():
    data = request.json
    user_id = data.get('userId')
    user_name = data.get('userName')
    message = data.get('message')

    if not user_id or not user_name or not message:
        return jsonify({'success': False, 'message': '缺少必要參數'})

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line_message = f"💬 {user_name}:\n{message}"

    if send_line_message_to_group(line_message):
        save_group_message(user_id, user_name, message, timestamp)
        return jsonify({'success': True, 'message': '訊息已發送'})
    else:
        return jsonify({'success': False, 'message': '發送失敗'})
