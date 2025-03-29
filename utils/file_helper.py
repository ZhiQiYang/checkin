import os
import json

def ensure_file_exists(filename, default_content):
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump(default_content, f)

def load_json(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_json_file(filename, default=None):
    """
    加載 JSON 文件，如果文件不存在或格式錯誤，返回默認值
    """
    try:
        return load_json(filename)
    except FileNotFoundError:
        if default is not None:
            return default
        raise
    except json.JSONDecodeError:
        if default is not None:
            return default
        raise

# 為向後兼容添加別名
