# utils/logger.py
import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(app=None):
    """設置日誌系統"""
    if not os.path.exists('logs'):
        os.mkdir('logs')
        
    # 配置根日誌記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 清除任何現有的處理器
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # 添加控制台處理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    root_logger.addHandler(console_handler)
    
    # 添加文件處理器
    file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    
    if app:
        app.logger.handlers = root_logger.handlers
        app.logger.setLevel(logging.INFO)
        app.logger.info('應用啟動')
        return app
    
    root_logger.info('日誌系統初始化完成')
    return root_logger

# 在 app.py 中加入
# from utils.logger import setup_logger
# app = setup_logger(app)
