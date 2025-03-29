from flask import Blueprint, render_template, request
import os

views_bp = Blueprint('views', __name__)

# 環境變數
LIFF_ID = os.environ.get('LIFF_ID')
GROUP_LIFF_ID = os.environ.get('GROUP_LIFF_ID')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

@views_bp.route('/checkin')
def checkin_page():
    return render_template('checkin.html', liff_id=LIFF_ID, google_maps_api_key=GOOGLE_MAPS_API_KEY)

@views_bp.route('/group')
def group_page():
    return render_template('group.html', liff_id=GROUP_LIFF_ID)

@views_bp.route('/personal-history')
def personal_history():
    from utils.file_helper import ensure_file_exists
    from config import CHECKIN_FILE
    import json
    from datetime import datetime, timedelta

    user_id = request.args.get('userId')
    if not user_id:
        return "請從 LINE 應用程式訪問此頁面", 400

    days_filter = request.args.get('dateRange', '7')
    ensure_file_exists(CHECKIN_FILE, {"records": []})
    with open(CHECKIN_FILE, 'r') as f:
        data = json.load(f)

    user_records = [r for r in data['records'] if r['user_id'] == user_id]

    if days_filter != 'all':
        try:
            days = int(days_filter)
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            user_records = [r for r in user_records if r['date'] >= cutoff_date]
        except ValueError:
            pass

    user_records.sort(key=lambda x: (x['date'], x['time']), reverse=True)

    has_map_records = any(
        'coordinates' in record and 
        record.get('coordinates', {}).get('latitude') and 
        record.get('coordinates', {}).get('longitude')
        for record in user_records
    )

    return render_template(
        'personal_history.html',
        records=user_records,
        days=days_filter,
        has_map_records=has_map_records,
        google_maps_api_key=GOOGLE_MAPS_API_KEY
    )
