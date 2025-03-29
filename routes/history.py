from flask import Blueprint, request, render_template
from utils.file_helper import load_json_file
from datetime import datetime, timedelta
from config import Config

history_bp = Blueprint('history', __name__)

@history_bp.route('/personal-history')
def personal_history():
    user_id = request.args.get('userId')
    if not user_id:
        return "請從 LINE 應用程式訪問此頁面", 400

    days_filter = request.args.get('dateRange', '7')

    data = load_json_file(Config.CHECKIN_FILE, default={"records": []})
    user_records = [r for r in data['records'] if r['user_id'] == user_id]

    # 其他代碼...
