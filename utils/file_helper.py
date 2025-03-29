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
