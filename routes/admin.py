# routes/admin.py
from flask import Blueprint, jsonify, request, render_template, redirect, url_for
from datetime import datetime
import os
import sqlite3
import json
import shutil
from config import Config
from services.notification_service import send_line_message_to_group

admin_bp = Blueprint('admin', __name__)

# 管理員ID列表，實際使用時請替換成真實的管理員ID
ADMIN_IDS = ['U123456789abcdef', 'U987654321abcdef']

def is_admin(user_id):
    """檢查是否為管理員"""
    return user_id in ADMIN_IDS

@admin_bp.route('/admin')
def admin_panel():
    """管理面板首頁"""
    user_id = request.args.get('userId')
    if not user_id or not is_admin(user_id):
        return "權限不足", 403
    
    return render_template('admin.html', user_id=user_id)

@admin_bp.route('/api/admin/system-info')
def system_info():
    """獲取系統信息"""
    user_id = request.args.get('userId')
    if not user_id or not is_admin(user_id):
        return jsonify({"error": "權限不足"}), 403
    
    try:
        # 收集系統信息
        import platform
        import psutil
        
        # 數據庫統計
        conn = sqlite3.connect(Config.DB_PATH)
        c = conn.cursor()
        
        # 打卡記錄統計
        c.execute("SELECT COUNT(*) FROM checkin_records")
        checkin_count = c.fetchone()[0]
        
        # 今日打卡統計
        today = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM checkin_records WHERE date = ?", (today,))
        today_count = c.fetchone()[0]
        
        # 用戶統計
        c.execute("SELECT COUNT(*) FROM users")
        user_count = c.fetchone()[0]
        
        # 獲取系統資源使用情況
        system_info = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage('/').percent,
            "system_uptime": datetime.now() - datetime.fromtimestamp(psutil.boot_time()),
            "db_stats": {
                "checkin_count": checkin_count,
                "today_count": today_count,
                "user_count": user_count
            }
        }
        
        conn.close()
        
        return jsonify(system_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@admin_bp.route('/api/admin/backup-db', methods=['POST'])
def backup_db():
    """備份數據庫"""
    user_id = request.json.get('userId')
    if not user_id or not is_admin(user_id):
        return jsonify({"success": False, "message": "權限不足"}), 403
    
    try:
        # 創建備份目錄
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
        
        # 生成備份文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"{backup_dir}/checkin_backup_{timestamp}.db"
        
        # 複製數據庫文件
        shutil.copy2(Config.DB_PATH, backup_file)
        
        # 發送通知
        message = f"✅ 數據庫備份成功\n📂 備份文件: {backup_file}\n🕒 時間: {timestamp}"
        
        return jsonify({
            "success": True,
            "message": message,
            "backup_file": backup_file,
            "timestamp": timestamp
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"備份失敗: {str(e)}"}), 500

@admin_bp.route('/api/admin/broadcast', methods=['POST'])
def broadcast_message():
    """發送全群廣播消息"""
    data = request.json
    user_id = data.get('userId')
    message = data.get('message')
    
    if not user_id or not is_admin(user_id):
        return jsonify({"success": False, "message": "權限不足"}), 403
    
    if not message:
        return jsonify({"success": False, "message": "消息不能為空"}), 400
    
    try:
        # 添加廣播標記
        broadcast_message = f"📢 系統公告\n{message}\n\n🕒 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # 發送到群組
        result = send_line_message_to_group(broadcast_message)
        
        if result:
            return jsonify({
                "success": True,
                "message": "廣播消息已發送"
            })
        else:
            return jsonify({
                "success": False,
                "message": "發送廣播消息失敗"
            })
    except Exception as e:
        return jsonify({"success": False, "message": f"廣播失敗: {str(e)}"}), 500

@admin_bp.route('/api/admin/clear-cache', methods=['POST'])
def clear_cache():
    """清理系統缓存"""
    user_id = request.json.get('userId')
    if not user_id or not is_admin(user_id):
        return jsonify({"success": False, "message": "權限不足"}), 403
    
    try:
        # 清理臨時文件
        temp_files = 0
        for root, dirs, files in os.walk('logs'):
            for file in files:
                if file.endswith('.log.1') or file.endswith('.bak') or file.endswith('.tmp'):
                    os.remove(os.path.join(root, file))
                    temp_files += 1
        
        # 清理過期備份
        backup_limit = 5  # 保留最近5個備份
        backup_dir = 'backups'
        if os.path.exists(backup_dir):
            backups = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.endswith('.db')]
            backups.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            if len(backups) > backup_limit:
                for old_backup in backups[backup_limit:]:
                    os.remove(old_backup)
        
        return jsonify({
            "success": True,
            "message": f"缓存清理完成，已刪除 {temp_files} 個臨時文件",
            "details": {
                "temp_files_removed": temp_files,
                "backups_kept": backup_limit
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"清理缓存失敗: {str(e)}"}), 500

@admin_bp.route('/admin/logs')
def view_logs():
    """查看系統日誌"""
    user_id = request.args.get('userId')
    if not user_id or not is_admin(user_id):
        return "權限不足", 403
    
    try:
        log_file = 'logs/app.log'
        if not os.path.exists(log_file):
            return "日誌文件不存在", 404
        
        with open(log_file, 'r', encoding='utf-8') as f:
            # 讀取最後1000行
            lines = f.readlines()[-1000:]
            log_content = ''.join(lines)
        
        return render_template('logs.html', 
                              log_content=log_content, 
                              user_id=user_id,
                              log_file=log_file,
                              generated_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    except Exception as e:
        return f"讀取日誌失敗: {str(e)}", 500

# 新增此代碼到 app.py 的 create_app 函數中註冊藍圖部分
# from routes.admin import admin_bp
# app.register_blueprint(admin_bp)
