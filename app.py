from flask import Flask
from config import APP_URL, PING_INTERVAL
from db import init_db
from utils.ping_thread import start_keep_alive_thread
from routes.api import api_bp
from routes.webhook import webhook_bp
from routes.views import views_bp
from routes.rich_menu import rich_menu_bp

import os
import threading
import time

# 建立 Flask 應用
app = Flask(__name__)

# 初始化資料庫
init_db()

# 註冊 Blueprint
app.register_blueprint(api_bp)
app.register_blueprint(webhook_bp)
app.register_blueprint(views_bp)
app.register_blueprint(rich_menu_bp)

# 健康檢查
@app.route('/')
def index():
    return "打卡系統運行中!"

@app.route('/ping', methods=['GET'])
def ping():
    from datetime import datetime
    return {"status": "alive", "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

# 如果是主程式運行，則啟動保活機制與伺服器
if __name__ == '__main__':
    if os.path.exists('static/rich_menu.jpg'):
        from routes.rich_menu import init_rich_menu_process
        init_rich_menu_process()

    # 啟動保活機制
    start_keep_alive_thread(APP_URL, PING_INTERVAL)

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
