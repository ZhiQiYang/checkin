from flask import Blueprint, jsonify
from services.rich_menu_service import (
    test_rich_menu_process,
    init_rich_menu_process
)

rich_menu_bp = Blueprint('rich_menu', __name__)

@rich_menu_bp.route('/test-rich-menu', methods=['GET'])
def test_rich_menu():
    success = test_rich_menu_process()
    if success:
        return jsonify({"success": True, "message": "Rich Menu 測試成功！"})
    else:
        return jsonify({"success": False, "message": "Rich Menu 測試失敗，請查看日誌"})

def test_rich_menu_process():
    try:
        response = requests.get(
            'https://api.line.me/v2/bot/richmenu/list',
            headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Rich Menu 測試錯誤: {e}")
        return False

@rich_menu_bp.route('/init-rich-menu', methods=['GET'])
def init_rich_menu():
    success, message = init_rich_menu_process()
    return jsonify({"success": success, "message": message})
