# app.py
from flask import Flask
from config import Config
from db import init_db
from utils.ping_thread import start_keep_alive_thread
from utils.logger import setup_logger
from routes.export import export_bp

# 添加到 app.py 的 create_app 函數開始處
from db.update_db import update_database
update_database()  # 確保數據庫結構正確
import traceback

@app.errorhandler(500)
def internal_error(error):
    app.logger.error('伺服器錯誤: %s\n%s', str(error), traceback.format_exc())
    return "伺服器內部錯誤，請查看日誌獲取詳情", 500

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 檢查並創建必要的檔案
    from utils.file_helper import ensure_file_exists
    print("檔案檢查完成")
    
    # 初始化資料庫
    init_db()
    
    # 註冊藍圖
    from routes.api import api_bp
    from routes.webhook import webhook_bp
    from routes.rich_menu import rich_menu_bp
    from routes.history import history_bp
    from routes.group import group_bp
    from routes.views import views_bp
    
    app.register_blueprint(export_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(rich_menu_bp)
    app.register_blueprint(history_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(views_bp)
    
    # 預設路由
    @app.route('/')
    def index():
        return "✅ 打卡系統運行中！"

    @app.route('/ping')
    def ping():
        from datetime import datetime
        return {"status": "alive", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, 200
    
    # 錯誤處理
    @app.errorhandler(404)
    def not_found_error(error):
        return "頁面不存在", 404

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
        return result
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error('服務器錯誤: %s', str(error))
        return "伺服器內部錯誤", 500
    
    # 啟動保活線程
    if not app.debug:
        start_keep_alive_thread(app.config['APP_URL'], app.config['KEEP_ALIVE_INTERVAL'])
    
    return app

# 入口點
app = create_app()
app = setup_logger(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=app.config['PORT'], debug=app.config['DEBUG'])
