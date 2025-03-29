import threading
import time
import requests

def keep_alive(app_url: str, interval: int):
    """定期發送請求到指定網址來保持服務活躍"""
    while True:
        try:
            response = requests.get(f"{app_url}/ping")
            print(f"[KeepAlive] Ping sent. Status: {response.status_code}")
        except Exception as e:
            print(f"[KeepAlive] Ping failed: {e}")
        time.sleep(interval)

def start_keep_alive_thread(app_url: str, interval: int):
    thread = threading.Thread(target=keep_alive, args=(app_url, interval), daemon=True)
    thread.start()
    print("[KeepAlive] Background thread started.")
