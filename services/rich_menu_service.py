# services/rich_menu_service.py
import os
import requests
from config import Config

def create_rich_menu():
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

    response = requests.post(
        'https://api.line.me/v2/bot/richmenu',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
        },
        json=rich_menu_data
    )

    if response.status_code == 200:
        return response.json()["richMenuId"]
    else:
        print(f"創建 Rich Menu 失敗: {response.text}")
        return None

def upload_rich_menu_image(rich_menu_id, image_path='static/rich_menu.jpg'):
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()

        response = requests.post(
            f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers={
                'Content-Type': 'image/jpeg',
                'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            data=image_data
        )

        return response.status_code == 200
    except Exception as e:
        print(f"上傳 Rich Menu 圖片錯誤: {e}")
        return False

def set_default_rich_menu(rich_menu_id):
    response = requests.post(
        f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
        headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
    )
    return response.status_code == 200

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

def init_rich_menu_process():
    try:
        # 刪除現有的 Rich Menu
        response = requests.get(
            'https://api.line.me/v2/bot/richmenu/list',
            headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
        )
        if response.status_code == 200:
            for menu in response.json().get("richmenus", []):
                requests.delete(
                    f'https://api.line.me/v2/bot/richmenu/{menu["richMenuId"]}',
                    headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
                )

        # 創建新的 Rich Menu
        rich_menu_id = create_rich_menu()
        if not rich_menu_id:
            return False, "創建 Rich Menu 失敗"

        # 上傳 Rich Menu 圖片
        if not upload_rich_menu_image(rich_menu_id):
            return False, "上傳 Rich Menu 圖片失敗"

        # 設置為默認 Rich Menu
        if not set_default_rich_menu(rich_menu_id):
            return False, "設置默認 Rich Menu 失敗"

        return True, "Rich Menu 初始化成功"
    except Exception as e:
        print(f"初始化 Rich Menu 錯誤: {e}")
        return False, f"初始化 Rich Menu 錯誤: {e}"
