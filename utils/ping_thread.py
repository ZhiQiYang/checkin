import threading
import time
import requests
from config import APP_URL

PING_INTERVAL = 840

def keep_alive():
    while True:
        try:
            res = requests.get(f"{APP_URL}/ping")
            print(f"[PING] Status: {res.status_code}")
        except Exception as e:
            print(f"[PING] Failed: {e}")
        time.sleep(PING_INTERVAL)

def start_keep_alive_thread():
    thread = threading.Thread(target=keep_alive, daemon=True)
    thread.start()
