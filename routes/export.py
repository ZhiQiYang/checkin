# routes/export.py
from flask import Blueprint, request, send_file, jsonify, render_template
from services.export_service import export_checkin_records_to_excel
from datetime import datetime, timedelta
import os

export_bp = Blueprint('export', __name__)

@export_bp.route('/export/checkin-records', methods=['GET'])
def export_checkin_records():
    user_id = request.args.get('userId')
    date_range = request.args.get('dateRange', '7')
    
    # 處理日期範圍
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    if date_range == 'all':
        date_from = None
    else:
        days = int(date_range)
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 生成Excel檔案
    excel_file = export_checkin_records_to_excel(user_id, date_from, date_to)
    
    if not excel_file or not os.path.exists(excel_file):
        return jsonify({'success': False, 'message': '沒有找到符合條件的打卡記錄'}), 404
    
    # 返回檔案
    return send_file(excel_file, as_attachment=True)

@export_bp.route('/export-form')
def export_form():
    user_id = request.args.get('userId')
    if not user_id:
        return "請從 LINE 應用程式訪問此頁面", 400
    
    return render_template('export_form.html', user_id=user_id)
