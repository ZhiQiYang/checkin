from flask import Flask
from config import Config
from db import init_db
from utils.ping_thread import start_keep_alive_thread

# 載入路由模組
from routes.api import api_bp
from routes.webhook import webhook_bp
from routes.rich_menu import rich_menu_bp
from routes.history import history_bp
from routes.group import group_bp
from routes.views import views_bp

app = Flask(__name__)
app.config.from_object(Config)

# 初始化資料庫
init_db()

# 註冊 Blueprint 路由
app.register_blueprint(api_bp)
app.register_blueprint(webhook_bp)
app.register_blueprint(rich_menu_bp)
app.register_blueprint(history_bp)
app.register_blueprint(group_bp)
app.register_blueprint(views_bp)

# 預設首頁和健康檢查
@app.route('/')
def index():
    return "✅ 打卡系統運行中！"

@app.route('/ping')
def ping():
    from datetime import datetime
    return {"status": "alive", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}, 200

if __name__ == '__main__':
    # 啟動保活線程
    start_keep_alive_thread()

    # 啟動應用
    app.run(host='0.0.0.0', port=int(Config.PORT), debug=False)
