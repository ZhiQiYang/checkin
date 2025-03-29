# app.py
from flask import Flask
from config import Config
from db import init_db
from utils.ping_thread import start_keep_alive_thread
from utils.logger import setup_logger

def create_app(config_class=Config):
    def check_files():
    # 檢查並創建必要的檔案
    from utils.file_helper import ensure_file_exists
    ensure_file_exists("checkin_records.json", {"records": []})
    ensure_file_exists("group_messages.json", {"messages": []})
    print("檔案檢查完成")
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # 初始化資料庫
    init_db()
    
    # 註冊藍圖
    from routes.api import api_bp
    from routes.webhook import webhook_bp
    from routes.rich_menu import rich_menu_bp
    from routes.history import history_bp
    from routes.group import group_bp
    from routes.views import views_bp
    
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
