from flask import Flask
from app.routes.checkin import checkin_bp
from app.routes.group import group_bp
from app.routes.webhook import webhook_bp
from app.routes.richmenu import richmenu_bp
from app.routes.export import export_bp
from app.db import init_db

def create_app():
    app = Flask(__name__)

    init_db()

    app.register_blueprint(checkin_bp)
    app.register_blueprint(group_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(richmenu_bp)
    app.register_blueprint(export_bp)

    return app
