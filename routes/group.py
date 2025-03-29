from flask import Blueprint, jsonify, request
from datetime import datetime
from services.notification_service import send_line_message_to_group

group_bp = Blueprint('group', __name__)

@group_bp.route('/api/group/messages', methods=['GET'])
def get_group_messages():
    count = int(request.args.get('count', 20))
    messages = get_recent_messages(count)
    return jsonify({
        'success': True,
        'messages': messages
    })

@group_bp.route('/api/group/send', methods=['POST'])
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
    group_message = f"\U0001F4AC {user_name}:\n{message}"

    sent = send_line_message_to_group(group_message)
    if sent:
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
