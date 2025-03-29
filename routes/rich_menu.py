from flask import Blueprint, jsonify
import requests
from config import Config
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

@rich_menu_bp.route('/init-rich-menu', methods=['GET'])
def init_rich_menu():
    success, message = init_rich_menu_process()
    return jsonify({"success": success, "message": message})
