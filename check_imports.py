# check_imports.py
import importlib
import os
import sys

def check_file(file_path):
    """檢查單個文件的導入"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 尋找所有導入語句
    import_lines = [line.strip() for line in content.split('\n') 
                   if line.strip().startswith('from ') or line.strip().startswith('import ')]
    
    for line in import_lines:
        try:
            exec(line)
            print(f"✅ {line}")
        except Exception as e:
            print(f"❌ {line} - Error: {e}")

def scan_directory(directory):
    """掃描目錄中所有 Python 文件"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f"\n檢查文件: {file_path}")
                check_file(file_path)

# 添加當前目錄到 Python 路徑
sys.path.append('.')

# 掃描所有 Python 文件
scan_directory('.')
