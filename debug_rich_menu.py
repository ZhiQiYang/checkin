import os
import requests
import json
from dotenv import load_dotenv
import sys
from PIL import Image

# 載入環境變數
load_dotenv()

# 獲取 LINE API 設置
MESSAGING_CHANNEL_ACCESS_TOKEN = os.environ.get('MESSAGING_CHANNEL_ACCESS_TOKEN')

# 驗證圖片
def validate_image(image_path):
    print(f"驗證圖片: {image_path}")
    
    # 檢查檔案是否存在
    if not os.path.exists(image_path):
        print(f"❌ 錯誤: 檔案不存在 - {image_path}")
        return False
    
    # 檢查檔案大小
    file_size = os.path.getsize(image_path)
    print(f"圖片大小: {file_size / 1024:.2f} KB")
    
    if file_size > 1024 * 1024:  # 1MB
        print(f"❌ 錯誤: 圖片太大 ({file_size / 1024:.2f} KB)，必須小於 1024 KB")
        return False
    
    # 檢查圖片尺寸和格式
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            format = img.format
            print(f"圖片尺寸: {width}x{height} 像素")
            print(f"圖片格式: {format}")
            
            if width != 2500 or height != 1686:
                print(f"❌ 錯誤: 圖片尺寸必須為 2500x1686 像素")
                return False
            
            if format not in ['JPEG', 'PNG']:
                print(f"❌ 錯誤: 圖片格式必須為 JPEG 或 PNG")
                return False
    except Exception as e:
        print(f"❌ 錯誤: 無法讀取圖片 - {str(e)}")
        return False
    
    print("✅ 圖片驗證通過")
    return True

# 驗證令牌
def validate_token():
    print(f"驗證 Channel Access Token")
    
    if not MESSAGING_CHANNEL_ACCESS_TOKEN:
        print("❌ 錯誤: 未設置 MESSAGING_CHANNEL_ACCESS_TOKEN 環境變數")
        return False
    
    # 測試 token 有效性
    response = requests.get(
        'https://api.line.me/v2/bot/info',
        headers={
            'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
        }
    )
    
    if response.status_code == 200:
        print("✅ Token 驗證通過")
        return True
    else:
        print(f"❌ 錯誤: Token 無效 - 狀態碼 {response.status_code}")
        print(f"回應內容: {response.text}")
        return False

# 創建 Rich Menu 並返回詳細日誌
def create_test_rich_menu():
    print("測試創建 Rich Menu...")
    
    # 定義一個最簡單的 Rich Menu
    rich_menu_data = {
        "size": {
            "width": 2500,
            "height": 1686
        },
        "selected": True,
        "name": "測試選單",
        "chatBarText": "測試選單",
        "areas": [
            {
                "bounds": {
                    "x": 0,
                    "y": 0,
                    "width": 2500,
                    "height": 1686
                },
                "action": {
                    "type": "message",
                    "text": "測試"
                }
            }
        ]
    }
    
    # 發送請求
    try:
        response = requests.post(
            'https://api.line.me/v2/bot/richmenu',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            json=rich_menu_data
        )
        
        print(f"API 回應狀態碼: {response.status_code}")
        print(f"API 回應內容: {response.text}")
        
        if response.status_code == 200:
            rich_menu_id = response.json().get("richMenuId")
            print(f"✅ 成功創建 Rich Menu: {rich_menu_id}")
            return rich_menu_id
        else:
            print("❌ 創建 Rich Menu 失敗")
            return None
    except Exception as e:
        print(f"❌ 異常: {str(e)}")
        return None

# 測試上傳圖片
def test_upload_image(rich_menu_id, image_path):
    print(f"測試上傳圖片 {image_path} 到 Rich Menu {rich_menu_id}...")
    
    # 確定 Content-Type
    content_type = "image/jpeg"
    if image_path.lower().endswith('.png'):
        content_type = "image/png"
    
    print(f"使用 Content-Type: {content_type}")
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        response = requests.post(
            f'https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content',
            headers={
                'Content-Type': content_type,
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            },
            data=image_data
        )
        
        print(f"API 回應狀態碼: {response.status_code}")
        print(f"API 回應內容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 成功上傳圖片")
            return True
        else:
            print("❌ 上傳圖片失敗")
            return False
    except Exception as e:
        print(f"❌ 異常: {str(e)}")
        return False

# 測試設置為默認 Rich Menu
def test_set_default(rich_menu_id):
    print(f"測試設置 Rich Menu {rich_menu_id} 為默認...")
    
    try:
        response = requests.post(
            f'https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}',
            headers={
                'Authorization': f'Bearer {MESSAGING_CHANNEL_ACCESS_TOKEN}'
            }
        )
        
        print(f"API 回應狀態碼: {response.status_code}")
        print(f"API 回應內容: {response.text}")
        
        if response.status_code == 200:
            print("✅ 成功設置默認 Rich Menu")
            return True
        else:
            print("❌ 設置默認 Rich Menu 失敗")
            return False
    except Exception as e:
        print(f"❌ 異常: {str(e)}")
        return False

# 主程序
def main():
    print("=== LINE Rich Menu 診斷工具 ===\n")
    
    # 檢查圖片
    image_paths = [
        'static/rich_menu.jpg',
        'static/rich_menu.png',
        os.path.join(os.getcwd(), 'static', 'rich_menu.jpg'),
        os.path.join(os.getcwd(), 'static', 'rich_menu.png')
    ]
    
    valid_images = []
    for path in image_paths:
        if os.path.exists(path):
            if validate_image(path):
                valid_images.append(path)
    
    if not valid_images:
        print("\n❌ 錯誤: 找不到有效的圖片，請確保圖片格式正確且尺寸為 2500x1686")
        return
    
    # 檢查 token
    if not validate_token():
        return
    
    # 嘗試創建 Rich Menu
    rich_menu_id = create_test_rich_menu()
    if not rich_menu_id:
        return
    
    # 嘗試上傳圖片
    for image_path in valid_images:
        print(f"\n嘗試使用圖片: {image_path}")
        if test_upload_image(rich_menu_id, image_path):
            # 如果上傳成功，則設置為默認
            test_set_default(rich_menu_id)
            print(f"\n✅ 成功完成所有步驟，Rich Menu ID: {rich_menu_id}")
            return
    
    print("\n❌ 所有圖片都上傳失敗")

if __name__ == "__main__":
    main()
