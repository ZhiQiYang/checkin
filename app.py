# app.py
from flask import Flask, jsonify
from config import Config
from db import init_db
from utils.ping_thread import start_keep_alive_thread
from utils.logger import setup_logger
from routes.export import export_bp
import traceback
from services.scheduler_service import reminder_scheduler
import requests
import os
import time
from config import Config
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


os.environ['TZ'] = Config.TIMEZONE
time.tzset()  # 應用時區變更，只在 Unix/Linux 環境有效
# 從 update_db.py 導入更新函數
from db.update_db import update_database

def check_dependencies():
    """檢查關鍵依賴項的可用性，並記錄狀態"""
    dependency_status = {}
    
    # 檢查 pandas
    try:
        import pandas
        dependency_status["pandas"] = f"可用 (版本: {pandas.__version__})"
    except ImportError:
        dependency_status["pandas"] = "不可用"
    
    # 檢查 reportlab
    try:
        import reportlab
        dependency_status["reportlab"] = f"可用 (版本: {reportlab.Version})"
    except ImportError:
        dependency_status["reportlab"] = "不可用"
    
    # 檢查 openpyxl (Excel 支持)
    try:
        import openpyxl
        dependency_status["openpyxl"] = f"可用 (版本: {openpyxl.__version__})"
    except ImportError:
        dependency_status["openpyxl"] = "不可用"
    
    # 檢查 Google API
    try:
        import googleapiclient
        dependency_status["googleapiclient"] = "可用"
    except ImportError:
        dependency_status["googleapiclient"] = "不可用"
    
    # 輸出依賴項狀態
    print("\n=== 系統依賴項狀態 ===")
    for dep, status in dependency_status.items():
        print(f"{dep}: {status}")
    print("=======================\n")

def create_app(config_class=Config):
    # 檢查依賴項狀態
    check_dependencies()
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 檢查並創建必要的檔案
    from utils.file_helper import ensure_file_exists
    print("檔案檢查完成")
    
    # 檢查並更新數據庫結構（保留數據）
    try:
        update_database()
    except Exception as e:
        print(f"警告: 數據庫更新過程中出錯: {e}")
        print("將繼續使用現有數據庫結構")
    
    # 初始化資料庫（如果表不存在則創建）
    init_db()
    
    # 註冊藍圖
    from routes.api import api_bp
    from routes.webhook import webhook_bp
    from routes.rich_menu import rich_menu_bp
    from routes.history import history_bp
    from routes.group import group_bp
    from routes.views import views_bp
    from routes.admin import admin_bp
    
    app.register_blueprint(export_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(rich_menu_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(admin_bp)
    
    # 預設路由
    @app.route('/')
    def index():
        return "✅ 打卡系統運行中！"
    
    @app.route('/ping')
    def ping():
        from datetime import datetime
        return {"status": "alive", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, 200
    
    # 初始化提醒系統
    reminder_scheduler.start()
    
    # 調試端點
    @app.route('/debug-error')
    def debug_error():
        try:
            # 嘗試連接數據庫並查詢
            import sqlite3
            conn = sqlite3.connect(Config.DB_PATH)
            c = conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = c.fetchall()
            
            result = {"tables": [t[0] for t in tables]}
            
            # 檢查表結構
            for table in result["tables"]:
                c.execute(f"PRAGMA table_info({table})")
                columns = c.fetchall()
                result[f"{table}_columns"] = [col[1] for col in columns]
            
            conn.close()
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e), "traceback": traceback.format_exc()})
    
    # 錯誤處理
    @app.errorhandler(404)
    def not_found_error(error):
        return "頁面不存在", 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('服務器錯誤: %s', str(error), exc_info=True)
        
        # 增加對特定類型異常的處理
        if isinstance(error, sqlite3.OperationalError):
            # 數據庫連接問題
            return "數據庫連接錯誤，系統正在維護中", 500
        elif isinstance(error, requests.exceptions.RequestException):
            # LINE API 連接問題
            return "LINE 服務連接錯誤，請稍後再試", 500
        return "伺服器內部錯誤，請查看日誌獲取詳情", 500

    @app.route('/check-timezone')
    def check_timezone():
        import pytz
        import time
        from datetime import datetime
    
        # 獲取系統時區
        system_tz = time.tzname
    
        # 獲取配置的時區
        config_tz = Config.TIMEZONE if hasattr(Config, 'TIMEZONE') else 'Asia/Taipei'
    
        # 獲取當前 UTC 時間
        utc_now = datetime.now(pytz.utc)
    
        # 轉換到配置的時區
        config_time = utc_now.astimezone(pytz.timezone(config_tz))
    
        # 可用時區列表
        available_timezones = pytz.all_timezones
    
        return {
            "system_timezone": system_tz,
            "configured_timezone": config_tz,
            "utc_time": str(utc_now),
            "configured_timezone_time": str(config_time),
            "available_asia_timezones": [tz for tz in available_timezones if tz.startswith('Asia/')]
        }
    
    # 啟動保活線程
    if not app.debug:
        start_keep_alive_thread(app.config['APP_URL'], app.config['KEEP_ALIVE_INTERVAL'])
    
    return app

# 入口點
app = create_app()
app = setup_logger(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=app.config['DEBUG'])
