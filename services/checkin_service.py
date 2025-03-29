from datetime import datetime
from db.crud import save_checkin as db_save_checkin

def process_checkin(user_id, display_name, location, note=None, latitude=None, longitude=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    success, message = db_save_checkin(
        user_id, display_name, location, note, latitude, longitude
    )
    return success, message, timestamp
