from flask import Blueprint, request, render_template
from utils.file_helper import load_json_file
from datetime import datetime, timedelta
import os

history_bp = Blueprint('history', __name__)

CHECKIN_FILE = 'checkin_records.json'
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', '')

@history_bp.route('/personal-history')
def personal_history():
    user_id = request.args.get('userId')
    if not user_id:
        return "請從 LINE 應用程式訪問此頁面", 400

    days_filter = request.args.get('dateRange', '7')

    data = load_json_file(CHECKIN_FILE, default={"records": []})
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
