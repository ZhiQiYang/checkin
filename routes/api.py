from flask import Blueprint, request, jsonify
from services.checkin_service import save_checkin_record
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
    success, message = save_checkin_record(
        user_id, display_name, location,
        note=note, latitude=latitude, longitude=longitude
    )

    if success:
        notification = f"\u2705 {display_name} \u5df2\u65bc {timestamp} \u5b8c\u6210\u6253\u5361\n\ud83d\udccd \u4f4d\u7f6e: {location}"
        if note:
            notification += f"\n\ud83d\udcdd \u5099\u8a3b: {note}"
        if latitude and longitude:
            notification += f"\n\ud83d\uddd8\ufe0f https://www.google.com/maps?q={latitude},{longitude}"

        if not send_line_message_to_group(notification):
            message += " (\u901a\u77e5\u767c\u9001\u5931\u6557)"

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
    line_message = f"\ud83d\udcac {user_name}:\n{message}"

    if send_line_message_to_group(line_message):
        save_group_message(user_id, user_name, message, timestamp)
        return jsonify({'success': True, 'message': '訊息已發送'})
    else:
        return jsonify({'success': False, 'message': '發送失敗'})
