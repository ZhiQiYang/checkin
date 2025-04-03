# services/__init__.py
"""
服務層：提供各種業務邏輯服務
"""

from services.vocabulary_service import (
    get_daily_words, 
    format_daily_words, 
    add_vocabulary
)

from services.checkin_service import (
    record_checkin,
    get_user_records,
    get_today_records,
    get_checkin_statistics
)

# 添加事件服務
from services.event_service import EventService

__all__ = [
    'get_daily_words',
    'format_daily_words',
    'add_vocabulary',
    'record_checkin',
    'get_user_records',
    'get_today_records',
    'get_checkin_statistics',
    'EventService'
]
