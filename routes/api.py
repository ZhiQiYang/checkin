# routes/api.py

from flask import Blueprint, request, jsonify
from services.checkin_service import process_checkin as process_checkin_logic
from services.group_service import save_group_message, get_recent_messages
from services.notification_service import send_line_message_to_group, send_line_notification
from datetime import datetime
from utils.validator import validate_checkin_input
from db.crud import get_reminder_setting, update_reminder_setting

api_bp = Blueprint('api', __name__)

import sqlite3
from datetime import datetime
from config import Config

# 修復版 API 路由函數
@api_bp.route('/api/check-today-status', methods=['GET'])
def check_today_status():
    """檢查今天的打卡狀態 - 適配舊版前端"""
    try:
        user_id = request.args.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'message': '缺少用戶ID'}), 400
        
        # 獲取今天日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 連接數據庫
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # 檢查今天是否有上班打卡
        c.execute('''
            SELECT * FROM checkin_records 
            WHERE user_id = ? AND date = ? AND checkin_type = ?
        ''', (user_id, today, '上班'))
        checkin_in = c.fetchone() is not None
        
        # 檢查今天是否有下班打卡
        c.execute('''
            SELECT * FROM checkin_records 
            WHERE user_id = ? AND date = ? AND checkin_type = ?
        ''', (user_id, today, '下班'))
        checkin_out = c.fetchone() is not None
        
        conn.close()
        
        # 返回結果
        return jsonify({
            'has_checkin_in': checkin_in,
            'has_checkin_out': checkin_out
        })
    except Exception as e:
        print(f"檢查今天打卡狀態出錯: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/checkin', methods=['POST'])
def handle_checkin():
    try:
        data = request.json
        
        # 調試信息
        print(f"收到打卡請求: {data}")
        
        # 驗證輸入
        errors = validate_checkin_input(data)
        if errors:
            return jsonify({'success': False, 'message': ', '.join(errors)}), 400
        
        user_id = data.get('userId')
        display_name = data.get('displayName')
        location = data.get('location', '未提供位置')
        note = data.get('note')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        checkin_type = data.get('checkinType', '上班')  # 默認上班打卡

        success, message, timestamp = process_checkin_logic(
            user_id, display_name, location,
            note=note, latitude=latitude, longitude=longitude, 
            checkin_type=checkin_type
        )

        if success:
            notification = f"✅ {display_name} 已於 {timestamp} 完成{checkin_type}打卡\n📍 位置: {location}"
            if note:
                notification += f"\n📝 備註: {note}"
            if latitude and longitude:
                notification += f"\n🗺️ https://www.google.com/maps?q={latitude},{longitude}"

            if not send_line_message_to_group(notification):
                message += "（通知發送失敗）"

        return jsonify({'success': success, 'message': message})
    except Exception as e:
        print(f"處理打卡API請求時出錯: {str(e)}")
        return jsonify({'success': False, 'message': f'系統錯誤: {str(e)}'}), 500

# 提醒設置 API
@api_bp.route('/api/reminder/settings', methods=['GET'])
def get_reminder_settings():
    user_id = request.args.get('userId')
    if not user_id:
        return jsonify({'success': False, 'message': '缺少用戶ID'}), 400
    
    settings = get_reminder_setting(user_id)
    return jsonify({
        'success': True,
        'settings': settings
    })

@api_bp.route('/api/reminder/settings', methods=['POST'])
def update_reminder_settings():
    data = request.json
    user_id = data.get('userId')
    
    if not user_id:
        return jsonify({'success': False, 'message': '缺少用戶ID'}), 400
    
    success = update_reminder_setting(user_id, data)
    return jsonify({
        'success': success,
        'message': '設置已更新' if success else '更新設置失敗'
    })

@api_bp.route('/api/reminder/test', methods=['POST'])
def test_reminder():
    """測試發送提醒"""
    data = request.json
    user_id = data.get('userId')
    name = data.get('name', '用戶')
    reminder_type = data.get('type', '上班')
    
    if not user_id:
        return jsonify({'success': False, 'message': '缺少用戶ID'}), 400
    
    if reminder_type == '上班':
        message = f"⏰ 測試 - {name}，早安！您今天還沒有上班打卡，請記得打卡。"
    else:
        message = f"⏰ 測試 - {name}，下班時間到了！您今天還沒有下班打卡，請記得打卡。"
    
    success = send_line_notification(user_id, message)
    
    return jsonify({
        'success': success,
        'message': '測試提醒已發送' if success else '發送測試提醒失敗'
    })
# 在 routes/api.py 中添加新的API端點來檢查今日打卡狀態

@api_bp.route('/api/checkin/status', methods=['GET'])
def get_checkin_status():
    """檢查今天的打卡狀態 - 新版 API"""
    try:
        user_id = request.args.get('userId')
        if not user_id:
            return jsonify({'success': False, 'message': '缺少用戶ID'}), 400
        
        # 獲取今天日期
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 連接數據庫
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # 查詢今天的打卡記錄
        c.execute('''
            SELECT checkin_type, time 
            FROM checkin_records 
            WHERE user_id = ? AND date = ?
            ORDER BY time ASC
        ''', (user_id, today))
        
        records = c.fetchall()
        conn.close()
        
        # 構建打卡狀態
        checkin_status = {
            '上班': None,
            '下班': None
        }
        
        for record in records:
            checkin_type = record['checkin_type']
            if checkin_type in checkin_status:
                checkin_status[checkin_type] = record['time']
        
        return jsonify({
            'success': True,
            'date': today,
            'status': checkin_status
        })
    except Exception as e:
        print(f"獲取打卡狀態出錯: {str(e)}")
        return jsonify({'success': False, 'message': f'獲取打卡狀態失敗: {str(e)}'}), 500
