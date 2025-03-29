# db/storage.py
import json
import sqlite3
import threading
from datetime import datetime
from config import Config

# 使用線程鎖避免併發問題
json_lock = threading.Lock()

def ensure_file_exists(filename, default_content):
    """確保文件存在，如不存在則創建並寫入預設內容"""
    with json_lock:
        try:
            with open(filename, 'r') as f:
                json.load(f)  # 測試文件是否為有效的 JSON
        except (FileNotFoundError, json.JSONDecodeError):
            with open(filename, 'w') as f:
                json.dump(default_content, f, ensure_ascii=False, indent=2)

def load_json(filename, default=None):
    """加載 JSON 文件，處理可能的錯誤"""
    with json_lock:
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            if default is not None:
                ensure_file_exists(filename, default)
                return default
            raise
        except json.JSONDecodeError:
            if default is not None:
                ensure_file_exists(filename, default)
                return default
            raise

def save_json(filename, data):
    """保存數據到 JSON 文件"""
    with json_lock:
        with open(filename, 'w') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def get_db_connection():
    """獲取資料庫連接"""
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row  # 返回字典形式的結果
    return conn
