from flask import Blueprint, render_template, request
from datetime import datetime, timedelta
from config import GOOGLE_MAPS_API_KEY
from utils.file_helper import load_json

views_bp = Blueprint('views', __name__)

@views_bp.route('/checkin')
def checkin_page():
    return render_template('checkin.html', google_maps_api_key=GOOGLE_MAPS_API_KEY)

@views_bp.route('/group')
def group_page():
    return render_template('group.html')

@views_bp.route('/personal-history')
def personal_history():
    user_id = request.args.get('userId')
    if not user_id:
        return "請從 LINE 應用程式訪問此頁面", 400

    days_filter = request.args.get('dateRange', '7')
    data = load_json('checkin_records.json')
    records = [r for r in data['records'] if r['user_id'] == user_id]

    if days_filter != 'all':
        try:
            days = int(days_filter)
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
            records = [r for r in records if r['date'] >= cutoff_date]
        except ValueError:
            pass

    records.sort(key=lambda r: (r['date'], r['time']), reverse=True)

    has_map_records = any(
        'coordinates' in r and r['coordinates'].get('latitude') and r['coordinates'].get('longitude')
        for r in records
    )

    return render_template(
        'personal_history.html',
        records=records,
        days=days_filter,
        has_map_records=has_map_records,
        google_maps_api_key=GOOGLE_MAPS_API_KEY
    )
