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
