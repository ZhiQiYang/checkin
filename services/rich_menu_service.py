import os
import requests
from config import Config  # 導入 Config 類

# 建立 Rich Menu
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
            # 其他代碼...
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

    # 其他代碼...
