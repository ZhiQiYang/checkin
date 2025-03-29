from flask import Blueprint, request, jsonify
from app.services.notify_service import handle_event

webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook', methods=['POST'])
def webhook():
    try:
        body = request.get_json()
        events = body.get('events', [])
        for event in events:
            handle_event(event)
    except Exception as e:
        print(f"[Webhook Error] {e}")
    return 'OK'
