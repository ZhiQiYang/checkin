# routes/views.py
from flask import Blueprint, render_template, request
from config import Config

views_bp = Blueprint('views', __name__)

@views_bp.route('/checkin')
def checkin_page():
    return render_template('checkin.html', liff_id=Config.LIFF_ID, google_maps_api_key=Config.GOOGLE_MAPS_API_KEY)

@views_bp.route('/group')
def group_page():
    return render_template('group.html', liff_id=Config.GROUP_LIFF_ID)

@views_bp.route('/reminder-settings')
def reminder_settings():
    return render_template('reminder_settings.html', liff_id=Config.LIFF_ID)
