# utils/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(app):
    """設置日誌系統"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('應用啟動')
    
    return app

# 在 app.py 中加入
# from utils.logger import setup_logger
# app = setup_logger(app)
