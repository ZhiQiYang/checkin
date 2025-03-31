# utils/timezone.py
import pytz
from datetime import datetime
from config import Config

def get_timezone():
    """
    獲取系統設置的時區，如果沒有設置則使用默認的台灣時區
    """
    return pytz.timezone(Config.TIMEZONE if hasattr(Config, 'TIMEZONE') else 'Asia/Taipei')

def get_current_time():
    """
    獲取當前的本地時間
    """
    timezone = get_timezone()
    utc_now = datetime.now(pytz.utc)
    return utc_now.astimezone(timezone)

def get_date_string():
    """
    獲取當前日期字符串 (YYYY-MM-DD)
    """
    return get_current_time().strftime('%Y-%m-%d')

def get_time_string():
    """
    獲取當前時間字符串 (HH:MM:SS)
    """
    return get_current_time().strftime('%H:%M:%S')

def get_datetime_string():
    """
    獲取當前日期時間字符串 (YYYY-MM-DD HH:MM:SS)
    """
    return get_current_time().strftime('%Y-%m-%d %H:%M:%S')

def format_datetime(dt):
    """
    將datetime對象格式化為字符串 (YYYY-MM-DD HH:MM:SS)
    """
    if not dt.tzinfo:
        # 如果datetime對象沒有時區信息，將其轉換為當前時區
        timezone = get_timezone()
        dt = timezone.localize(dt)
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def parse_datetime(dt_string):
    """
    解析日期時間字符串為datetime對象，並添加時區信息
    """
    dt = datetime.strptime(dt_string, '%Y-%m-%d %H:%M:%S')
    timezone = get_timezone()
    return timezone.localize(dt)
