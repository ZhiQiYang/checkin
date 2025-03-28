import os
import requests
import json
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 獲取 LINE API 設置
MESSAGING_CHANNEL_ACCESS_TOKEN = os.environ.get('MESSAGING_CHANNEL_ACCESS_TOKEN')

# 用於記錄詳細信息的函數
def log_error(message, response=None):
    print(f"[ERROR] {message}")
    if response:
        print(f"狀態碼: {response.status_code}")
        print(f"回應內容: {response.text}")

# 建立 Rich Menu
def create_rich_menu():
    try:
        print("開始創建 Rich Menu...")
        # 定義 Rich Menu 結構
        rich_menu_data = {
            "size": {
                "width": 2500,
                "height": 1686
            },
            "selected": True,
            "name": "打卡系統選單",
            "chatBarText": "打開選單",
            "areas": [
                {
                    "bounds": {
                        "x": 0,
                        "y": 0,
                        "width": 1250,
                        "height": 843
                    },
                    "action": {
                        "type": "uri",
                        "uri": f"https://liff.line.me/{os.environ.get('LIFF_ID')}"
                    }
                },
                {
                    "bounds": {
                        "x": 1250,
                        "y": 0,
                        "width": 1250,
                        "height": 843
                    },
                    "action": {
                        "type": "uri",
                        "uri": f"https://liff.line.me/{os.environ.get('GROUP_LIFF_ID')}"
                    }
                },
                {
                    "bounds": {
                        "x": 0,
                        "y": 843,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "!打卡報表"
                    }
                },
                {
                    "bounds": {
                        "x": 833,
                        "y": 843,
                        "width": 833,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "!幫助"
                    }
                },
                {
                    "bounds": {
                        "x": 1666,
                        "y": 843,
                        "width": 834,
                        "height": 843
                    },
                    "action": {
                        "type": "message",
                        "text": "!快速打卡"
                    }
                }
            ]
        }
        
        # 發送請求創建 Rich Menu
        response = requests.post(
            'https://api.line.me/v2/bot/richmenu',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json=rich_menu_data
        )
        
        # 檢查回應
        if response.status_code == 200:
            rich_menu_id = response.json()["richMenuId"]
            print(f"成功創建 Rich Menu ID: {rich_menu_id}")
            return rich_menu_id
        else:
            log_error("創建 Rich Menu 失敗", response)
            return None
            
    except Exception as e:
        log_error(f"創建 Rich Menu 發生例外: {str(e)}")
        return None

# 上傳 Rich Menu 圖片
def upload_rich_menu_image(rich_menu_id, image_path):
    try:
        print(f"開始上傳 Rich Menu 圖片: {image_path}")
        
        # 檢查檔案是否存在
        if not os.path.exists(image_path):
            log_error(f"圖片檔案不存在: {image_path}")
            return False
            
        # 獲取檔案大小
        file_size = os.path.getsize(image_path)
        print(f"圖片檔案大小: {file_size} 位元組")
        
        # 讀取圖片
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # 判斷圖片類型
        content_type = "image/jpeg"
        if image_path.lower().endswith('.png'):
            content_type = "image/png"
            
        print(f"使用的 Content-Type: {content_type}")
        
        # 上傳圖片
        response = requests.post(
            f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers={
                'Content-Type': content_type,
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            data=image_data
        )
        
        # 檢查回應
        if response.status_code == 200:
            print("成功上傳 Rich Menu 圖片")
            return True
        else:
            log_error("上傳 Rich Menu 圖片失敗", response)
            return False
            
    except Exception as e:
        log_error(f"上傳 Rich Menu 圖片發生例外: {str(e)}")
        return False

# 設置為默認 Rich Menu
def set_default_rich_menu(rich_menu_id):
    try:
        print(f"開始設置默認 Rich Menu ID: {rich_menu_id}")
        
        response = requests.post(
            f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
            headers={
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            }
        )
        
        # 檢查回應
        if response.status_code == 200:
            print("成功設置默認 Rich Menu")
            return True
        else:
            log_error("設置默認 Rich Menu 失敗", response)
            return False
            
    except Exception as e:
        log_error(f"設置默認 Rich Menu 發生例外: {str(e)}")
        return False

# 獲取 Rich Menu 列表
def get_rich_menu_list():
    try:
        print("獲取 Rich Menu 列表...")
        
        response = requests.get(
            'https://api.line.me/v2/bot/richmenu/list',
            headers={
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            }
        )
        
        # 檢查回應
        if response.status_code == 200:
            rich_menus = response.json().get("richmenus", [])
            print(f"找到 {len(rich_menus)} 個 Rich Menu")
            for menu in rich_menus:
                print(f"ID: {menu['richMenuId']}, 名稱: {menu['name']}")
            return rich_menus
        else:
            log_error("獲取 Rich Menu 列表失敗", response)
            return []
            
    except Exception as e:
        log_error(f"獲取 Rich Menu 列表發生例外: {str(e)}")
        return []

# 刪除 Rich Menu
def delete_rich_menu(rich_menu_id):
    try:
        print(f"開始刪除 Rich Menu ID: {rich_menu_id}")
        
        response = requests.delete(
            f'https://api.line.me/v2/bot/richmenu/{rich_menu_id}',
            headers={
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            }
        )
        
        # 檢查回應
        if response.status_code == 200:
            print(f"成功刪除 Rich Menu ID: {rich_menu_id}")
            return True
        else:
            log_error(f"刪除 Rich Menu ID: {rich_menu_id} 失敗", response)
            return False
            
    except Exception as e:
        log_error(f"刪除 Rich Menu 發生例外: {str(e)}")
        return False

# 完整測試流程
def test_rich_menu_process():
    # 1. 獲取現有 Rich Menu 列表
    existing_menus = get_rich_menu_list()
    
    # 2. 刪除現有的 Rich Menu (如果有)
    for menu in existing_menus:
        delete_rich_menu(menu['richMenuId'])
    
    # 3. 創建新的 Rich Menu
    rich_menu_id = create_rich_menu()
    if not rich_menu_id:
        print("無法繼續測試，因為 Rich Menu 創建失敗")
        return False
    
    # 4. 嘗試不同的圖片路徑
    image_paths = [
        'static/rich_menu.jpg',
        'static/rich_menu.png',
        os.path.join(os.getcwd(), 'static', 'rich_menu.jpg'),
        os.path.join(os.getcwd(), 'static', 'rich_menu.png')
    ]
    
    success = False
    for path in image_paths:
        if os.path.exists(path):
            print(f"找到圖片: {path}")
            if upload_rich_menu_image(rich_menu_id, path):
                success = True
                print(f"使用圖片 {path} 上傳成功")
                break
    
    if not success:
        print("所有圖片路徑都上傳失敗")
        return False
    
    # 5. 設置為默認 Rich Menu
    if not set_default_rich_menu(rich_menu_id):
        print("設置默認 Rich Menu 失敗")
        return False
    
    print("=== Rich Menu 測試完成，成功設置 ===")
    return True

# 主執行函數
if __name__ == "__main__":
    print("開始 Rich Menu 測試程序...")
    test_rich_menu_process()
