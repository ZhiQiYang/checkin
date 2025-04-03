#routes/rich_menu.py

from flask import Blueprint, jsonify, send_file, current_app
import os
import requests
import json
from config import Config
from services.rich_menu_service import (
    test_rich_menu_process,
    init_rich_menu_process,
    delete_all_rich_menus
)

rich_menu_bp = Blueprint('rich_menu', __name__)

@rich_menu_bp.route('/test-rich-menu', methods=['GET'])
def test_rich_menu():
    """測試Rich Menu是否正常工作"""
    success = test_rich_menu_process()
    return jsonify({
        'success': success,
        'message': '測試Rich Menu成功' if success else '測試Rich Menu失敗'
    })

@rich_menu_bp.route('/init-rich-menu', methods=['GET'])
def init_rich_menu():
    """初始化Rich Menu"""
    success, message = init_rich_menu_process()
    return jsonify({
        'success': success,
        'message': message
    })

@rich_menu_bp.route('/force-update-rich-menu', methods=['GET'])
def force_update_rich_menu():
    """強制更新Rich Menu - 刪除所有現有選單並創建新的選單"""
    current_app.logger.info("強制更新Rich Menu開始...")
    
    # 刪除所有現有Rich Menu
    delete_success = delete_all_rich_menus()
    if not delete_success:
        return jsonify({
            'success': False,
            'message': '刪除現有Rich Menu失敗，無法繼續更新'
        })
    
    # 初始化新的Rich Menu
    success, message = init_rich_menu_process()
    
    current_app.logger.info(f"強制更新Rich Menu結果: {success}, {message}")
    return jsonify({
        'success': success,
        'message': message,
        'delete_result': delete_success
    })

@rich_menu_bp.route('/check-rich-menu-image', methods=['GET'])
def check_rich_menu_image():
    """檢查Rich Menu圖片是否存在，並返回圖片資訊"""
    results = []
    
    # 檢查可能的圖片路徑
    possible_paths = [
        'static/rich_menu.png',
        './static/rich_menu.png',
        '../static/rich_menu.png',
        'static/rich_menu.jpg',
        './static/rich_menu.jpg',
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/rich_menu.png')
    ]
    
    current_dir = os.getcwd()
    
    # 檢查每個可能的路徑
    for path in possible_paths:
        if os.path.exists(path):
            try:
                file_size = os.path.getsize(path)
                absolute_path = os.path.abspath(path)
                results.append({
                    'path': path,
                    'exists': True,
                    'size': f"{file_size/1024:.2f} KB",
                    'absolute_path': absolute_path
                })
            except Exception as e:
                results.append({
                    'path': path,
                    'exists': True,
                    'error': str(e)
                })
        else:
            results.append({
                'path': path,
                'exists': False
            })
    
    return jsonify({
        'current_directory': current_dir,
        'config': {
            'messaging_token_length': len(Config.MESSAGING_CHANNEL_ACCESS_TOKEN) if Config.MESSAGING_CHANNEL_ACCESS_TOKEN else 0,
            'app_url': Config.APP_URL,
            'liff_id': Config.LIFF_ID,
            'group_liff_id': Config.GROUP_LIFF_ID
        },
        'results': results
    })

@rich_menu_bp.route('/rich-menu-info', methods=['GET'])
def rich_menu_info():
    """獲取Rich Menu的配置信息"""
    # 獲取指向靜態文件目錄的絕對路徑
    static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
    
    # 檢查靜態文件目錄下的內容
    static_files = []
    if os.path.exists(static_dir):
        static_files = os.listdir(static_dir)
    
    # 獲取Rich Menu的配置數據
    rich_menu_data = {
        "size": {"width": 2500, "height": 1686},
        "selected": True,
        "name": "打卡系統選單",
        "chatBarText": "打開選單",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 1250, "height": 843},
                "action": {"type": "uri", "uri": f"https://liff.line.me/{Config.LIFF_ID}"}
            },
            {
                "bounds": {"x": 1250, "y": 0, "width": 1250, "height": 843},
                "action": {"type": "uri", "uri": f"https://liff.line.me/{Config.GROUP_LIFF_ID}"}
            },
            {
                "bounds": {"x": 0, "y": 843, "width": 625, "height": 843},
                "action": {"type": "message", "text": "!打卡報表"}
            },
            {
                "bounds": {"x": 625, "y": 843, "width": 625, "height": 843},
                "action": {"type": "message", "text": "!幫助"}
            },
            {
                "bounds": {"x": 1250, "y": 843, "width": 625, "height": 843},
                "action": {"type": "message", "text": "!打卡"}
            },
            {
                "bounds": {"x": 1875, "y": 843, "width": 625, "height": 843},
                "action": {"type": "uri", "uri": f"{Config.APP_URL}/reminder-settings"}
            }
        ]
    }
    
    return jsonify({
        'static_directory': static_dir,
        'static_files': static_files,
        'rich_menu_config': rich_menu_data,
        'endpoints': {
            'test_rich_menu': f"{Config.APP_URL}/test-rich-menu",
            'init_rich_menu': f"{Config.APP_URL}/init-rich-menu",
            'force_update_rich_menu': f"{Config.APP_URL}/force-update-rich-menu",
            'check_rich_menu_image': f"{Config.APP_URL}/check-rich-menu-image"
        }
    })
