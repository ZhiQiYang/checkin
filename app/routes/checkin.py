from flask import Blueprint, request, jsonify
from datetime import datetime
from db import save_checkin
from app.utils.notify import send_line_message_to_group

checkin_bp = Blueprint('checkin', __name__)

@checkin_bp.route('/api/checkin', methods=['POST'])
def process_checkin():
    data = request.json
    user_id = data.get('userId')
    display_name = data.get('displayName')
    location = data.get('location', '未提供位置')
    note = data.get('note')
    latitude = data.get('latitude')
    longitude = data.get('longitude')

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    success, message = save_checkin(user_id, display_name, location, note, latitude, longitude)

    if success:
        notification_text = f"✅ {display_name} 已於 {timestamp} 完成打卡\n📍 位置: {location}"
        if note:
            notification_text += f"\n📝 備註: {note}"
        if latitude and longitude:
            notification_text += f"\n🗺️ https://www.google.com/maps?q={latitude},{longitude}"
        send_line_message_to_group(notification_text)

    return jsonify({'success': success, 'message': message})
