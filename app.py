# app.py
import os
import sys
import traceback
import requests
import time
import logging
from datetime import datetime

# --- 獲取app.py所在的目錄作為專案根目錄 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
# 專案根目錄就是app.py所在目錄
project_root = current_dir

# 將專案根目錄加到Python搜尋路徑的最前面
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 移除舊的路徑設置
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 打印系統路徑以供調試
print(f"DEBUG: Python sys.path: {sys.path}")
# ---

from flask import Flask, jsonify
from config import Config
from db import init_db
from utils.ping_thread import start_keep_alive_thread
from utils.logger import setup_logger
from routes.export import export_bp
from services.scheduler_service import reminder_scheduler

# 嘗試導入新的日誌配置，如果找不到則使用原有的setup_logger
try:
    from logging_config import setup_logging
    print("使用進階日誌系統 logging_config")
except ImportError:
    from utils.logger import setup_logger as setup_logging
    print("找不到logging_config模組，使用基本日誌系統 utils.logger")

# 設置時區
os.environ['TZ'] = 'Asia/Taipei'
# 根據平台決定是否調用 tzset
if hasattr(time, 'tzset'):
    time.tzset()  # 應用時區變更，只在 Unix/Linux 環境有效

# 從 update_db.py 導入更新函數
from db.update_db import update_database

# 導入所有必要的模型用於表創建檢查
try:
    from models import (
        User, CheckinRecord, Vocabulary, UserVocabulary,
        ReminderSetting, GroupMessage
    )
    print("成功導入所有模型類")
except ImportError as e:
    print(f"無法導入某些模型類: {e}")

# 導入詞彙服務
try:
    from services.vocabulary_service import init_vocabulary_database as init_vocab_db_with_data
    print("成功導入詞彙初始化服務")
except ImportError as e:
    print(f"無法導入詞彙初始化服務: {e}")

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
    # 初始化日誌系統
    logger = setup_logging()
    logger.info("應用程序啟動中...")
    
    # 檢查依賴項狀態
    check_dependencies()
    
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 使用新的日誌系統
    app.logger.handlers = logger.handlers
    app.logger.setLevel(logger.level)
    
    # 檢查並創建必要的檔案
    from utils.file_helper import ensure_file_exists
    app.logger.info("檔案檢查完成")
    
    # --- 修改數據庫初始化流程 ---
    # 1. 執行數據庫結構更新 (ALTER TABLE 等)
    try:
        update_database() # update_db.py 只應包含 ALTER TABLE 等遷移操作
        app.logger.info("數據庫結構更新檢查完成")
    except Exception as e:
        app.logger.error(f"警告: 數據庫更新過程中出錯: {e}")
        print(f"警告: 數據庫更新過程中出錯: {e}")
        print("將繼續嘗試確保表結構存在")
    
    # 2. 確保所有基礎表都存在 (CREATE TABLE IF NOT EXISTS)
    try:
        print("確保所有數據庫表存在...")
        # 確保模型已被導入
        if 'User' in globals():
            User.create_table_if_not_exists()
            CheckinRecord.create_table_if_not_exists()
            Vocabulary.create_table_if_not_exists()
            UserVocabulary.create_table_if_not_exists()
            ReminderSetting.create_table_if_not_exists()
            GroupMessage.create_table_if_not_exists()
            # 添加其他表...
            print("✅ 所有基本表結構已確認/創建")
        else:
            # 如果模型導入失敗，使用舊方法
            print("⚠️ 使用舊的init_db方法初始化數據庫")
            init_db()
    except Exception as e:
        app.logger.error(f"❌ 檢查/創建數據表時出錯: {e}")
        print(f"❌ 檢查/創建數據表時出錯: {e}")
        print("將嘗試使用舊的初始化方法")
        # 嘗試舊的初始化方法
        try:
            init_db()
        except Exception as e2:
            app.logger.error(f"❌ 舊的初始化方法也失敗: {e2}")
            print(f"❌ 舊的初始化方法也失敗: {e2}")
    
    # 3. 初始化詞彙數據 (包括填充默認詞彙)
    try:
        if 'init_vocab_db_with_data' in globals():
            init_vocab_db_with_data() # 這個函數負責創建表和填充數據
            print("✅ 詞彙數據庫初始化完成 (含預設資料)")
        else:
            print("⚠️ 未找到詞彙初始化函數，跳過詞彙初始化")
    except Exception as e:
        app.logger.error(f"❌ 詞彙數據庫初始化失敗: {e}")
        print(f"❌ 詞彙數據庫初始化失敗: {e}")
    # --- 結束修改數據庫初始化流程 ---
    
    # 註冊藍圖
    print("DEBUG: 正在註冊藍圖...")
    try:
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
        print("DEBUG: 藍圖註冊完成")
    except Exception as e:
        app.logger.error(f"註冊藍圖時出錯: {e}")
        print(f"註冊藍圖時出錯: {e}")
    
    # 預設路由
    @app.route('/')
    def index():
        return "✅ 打卡系統運行中！"
    
    @app.route('/ping')
    def ping():
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

# 如果需要額外設置app的logger
try:
    app = setup_logger(app)
except Exception as e:
    print(f"設置應用logger時出錯: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=app.config['DEBUG'])
