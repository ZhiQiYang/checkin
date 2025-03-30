# routes/export.py
from flask import Blueprint, request, send_file, jsonify, render_template, Response
from services.export_service import export_checkin_records_to_excel
from datetime import datetime, timedelta
import os
import sqlite3
import io
import csv
from config import Config

export_bp = Blueprint('export', __name__)

# 原有的路由函數
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
    
    # 生成Excel檔案到內存
    excel_buffer = export_checkin_records_to_excel(user_id, date_from, date_to)
    
    if not excel_buffer:
        return jsonify({'success': False, 'message': '沒有找到符合條件的打卡記錄'}), 404
    
    # 返回內存中的Excel文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return send_file(
        excel_buffer,
        as_attachment=True,
        download_name=f"checkin_records_{timestamp}.xlsx",
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@export_bp.route('/export-form')
def export_form():
    user_id = request.args.get('userId')
    if not user_id:
        return "請從 LINE 應用程式訪問此頁面", 400
    
    return render_template('export_form.html', user_id=user_id)

# 新增的路由函數
@export_bp.route('/export-text', methods=['GET'])
def export_text():
    user_id = request.args.get('userId')
    date_range = request.args.get('dateRange', '7')
    format_type = request.args.get('format', 'json')  # 'json' or 'csv'
    
    if not user_id:
        return jsonify({'success': False, 'message': '缺少用戶ID'})
    
    # 處理日期範圍
    date_to = datetime.now().strftime('%Y-%m-%d')
    
    if date_range == 'all':
        date_from = None
    else:
        days = int(date_range)
        date_from = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # 從數據庫獲取打卡記錄
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    if date_from:
        c.execute('''
            SELECT * FROM checkin_records 
            WHERE user_id = ? AND date >= ? 
            ORDER BY date DESC, time DESC
        ''', (user_id, date_from))
    else:
        c.execute('''
            SELECT * FROM checkin_records 
            WHERE user_id = ? 
            ORDER BY date DESC, time DESC
        ''', (user_id,))
    
    results = c.fetchall()
    conn.close()
    
    # 將記錄轉換為列表
    records = []
    for row in results:
        record = {}
        for key in row.keys():
            record[key] = row[key]
        records.append(record)
    
    if not records:
        return jsonify({'success': False, 'message': '沒有找到符合條件的打卡記錄'})
    
    # 根據格式類型返回
    if format_type == 'json':
        return jsonify({
            'success': True,
            'records': records
        })
    else:  # CSV
        # 構建 CSV 字符串
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
        
        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={"Content-disposition": f"attachment; filename=checkin_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
