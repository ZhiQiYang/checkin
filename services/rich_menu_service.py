# services/rich_menu_service.py
import os
import requests
import time
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

    print(f"正在創建Rich Menu...")
    print(f"LIFF_ID: {Config.LIFF_ID}, GROUP_LIFF_ID: {Config.GROUP_LIFF_ID}, APP_URL: {Config.APP_URL}")

    response = requests.post(
        'https://api.line.me/v2/bot/richmenu',
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
        },
        json=rich_menu_data
    )

    if response.status_code == 200:
        rich_menu_id = response.json()["richMenuId"]
        print(f"創建Rich Menu成功，ID: {rich_menu_id}")
        return rich_menu_id
    else:
        print(f"創建Rich Menu失敗: {response.status_code} {response.text}")
        return None

def upload_rich_menu_image(rich_menu_id, image_path=None):
    """
    上傳Rich Menu圖片
    
    Args:
        rich_menu_id: Rich Menu ID
        image_path: 圖片路徑，如果為None，會嘗試多個可能的路徑
    
    Returns:
        bool: 是否成功
    """
    # 如果沒有指定路徑，嘗試多個可能的路徑
    if not image_path:
        possible_paths = [
            'static/rich_menu.png',
            './static/rich_menu.png',
            '../static/rich_menu.png',
            'static/rich_menu.jpg',
            './static/rich_menu.jpg',
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '../static/rich_menu.png')
        ]
        
        # 找出第一個存在的路徑
        for path in possible_paths:
            if os.path.exists(path):
                image_path = path
                print(f"找到Rich Menu圖片: {path}")
                break
        
        if not image_path:
            print(f"❌ 無法找到Rich Menu圖片！嘗試了這些路徑: {possible_paths}")
            return False
    
    try:
        # 檢查檔案是否存在
        if not os.path.exists(image_path):
            print(f"❌ Rich Menu圖片不存在: {image_path}")
            print(f"當前目錄: {os.getcwd()}")
            return False
            
        # 確定圖片格式
        content_type = 'image/png' if image_path.endswith('.png') else 'image/jpeg'
        
        with open(image_path, 'rb') as f:
            image_data = f.read()
            
        print(f"正在上傳Rich Menu圖片: {image_path}, 大小: {len(image_data)/1024:.2f} KB, 格式: {content_type}")

        response = requests.post(
            f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers={
                'Content-Type': content_type,
                'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            data=image_data
        )

        if response.status_code != 200:
            print(f"❌ 上傳Rich Menu圖片失敗: {response.status_code} {response.text}")
            return False
            
        print(f"✅ 上傳Rich Menu圖片成功")
        return True
    except Exception as e:
        print(f"❌ 上傳Rich Menu圖片錯誤: {e}")
        return False

def set_default_rich_menu(rich_menu_id):
    """設置為預設選單"""
    print(f"正在設置Rich Menu為預設選單: {rich_menu_id}")
    
    response = requests.post(
        f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
        headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
    )
    
    if response.status_code == 200:
        print(f"✅ 設置預設Rich Menu成功")
        return True
    else:
        print(f"❌ 設置預設Rich Menu失敗: {response.status_code} {response.text}")
        return False

def delete_all_rich_menus():
    """刪除所有Rich Menu"""
    print("正在獲取所有Rich Menu列表...")
    
    response = requests.get(
        'https://api.line.me/v2/bot/richmenu/list',
        headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
    )
    
    if response.status_code != 200:
        print(f"❌ 獲取Rich Menu列表失敗: {response.status_code} {response.text}")
        return False
        
    menus = response.json().get("richmenus", [])
    print(f"找到 {len(menus)} 個Rich Menu")
    
    success = True
    for menu in menus:
        menu_id = menu["richMenuId"]
        print(f"正在刪除Rich Menu: {menu_id}")
        
        delete_response = requests.delete(
            f'https://api.line.me/v2/bot/richmenu/{menu_id}',
            headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
        )
        
        if delete_response.status_code == 200:
            print(f"✅ 刪除Rich Menu成功: {menu_id}")
        else:
            print(f"❌ 刪除Rich Menu失敗: {menu_id}, {delete_response.status_code} {delete_response.text}")
            success = False
            
    return success

def test_rich_menu_process():
    """測試Rich Menu API"""
    try:
        print("測試Rich Menu API...")
        
        response = requests.get(
            'https://api.line.me/v2/bot/richmenu/list',
            headers={'Authorization': f'Bearer {Config.MESSAGING_CHANNEL_ACCESS_TOKEN}'}
        )
        
        if response.status_code == 200:
            menus = response.json().get("richmenus", [])
            print(f"✅ 成功獲取Rich Menu列表，共有 {len(menus)} 個菜單")
            for menu in menus:
                print(f"  - ID: {menu['richMenuId']}, 名稱: {menu.get('name', '無名稱')}")
            return True
        else:
            print(f"❌ 獲取Rich Menu列表失敗: {response.status_code} {response.text}")
            return False
    except Exception as e:
        print(f"❌ Rich Menu測試錯誤: {e}")
        return False

def init_rich_menu_process():
    """初始化Rich Menu流程"""
    try:
        print("開始初始化Rich Menu流程...")
        
        # 步驟1: 刪除所有現有Rich Menu
        delete_all_rich_menus()
        
        # 等待一下，確保刪除操作完成
        time.sleep(1)
        
        # 步驟2: 創建新Rich Menu
        rich_menu_id = create_rich_menu()
        if not rich_menu_id:
            print("❌ 創建Rich Menu失敗，流程中止")
            return False, "創建Rich Menu失敗"
            
        # 步驟3: 上傳Rich Menu圖片
        if not upload_rich_menu_image(rich_menu_id):
            print("❌ 上傳Rich Menu圖片失敗，流程中止")
            return False, "上傳Rich Menu圖片失敗"
            
        # 等待一下，確保圖片上傳完成
        time.sleep(1)
        
        # 步驟4: 設置為預設Rich Menu
        if not set_default_rich_menu(rich_menu_id):
            print("❌ 設置預設Rich Menu失敗，流程中止")
            return False, "設置預設Rich Menu失敗"
            
        print("✅ Rich Menu初始化流程完成")
        return True, f"Rich Menu初始化成功，ID: {rich_menu_id}"
    except Exception as e:
        print(f"❌ 初始化Rich Menu錯誤: {e}")
        return False, f"初始化Rich Menu錯誤: {str(e)}"
