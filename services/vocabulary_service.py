"""
詞彙服務：提供詞彙學習相關的功能
"""

import random
import sqlite3
from datetime import datetime, timedelta
from models import Vocabulary, UserVocabulary, Database

def get_daily_words(user_id=None):
    """
    獲取用戶當日的學習詞彙
    
    Args:
        user_id: LINE用戶ID，如果為None則返回隨機詞彙
        
    Returns:
        包含詞彙信息的列表，每個詞彙包含英文、中文和難度
    """
    try:
        # 獲取當前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # 確保數據表存在
        Vocabulary.create_table_if_not_exists()
        UserVocabulary.create_table_if_not_exists()
        
        # 如果沒有用戶ID，直接返回隨機詞彙
        if not user_id:
            words = Vocabulary.get_random_words(count=3)
            return [{
                'english': word['english_word'],
                'chinese': word['chinese_translation'],
                'difficulty': word['difficulty']
            } for word in words]
        
        # 查詢用戶今日詞彙
        words = UserVocabulary.get_user_daily_words(user_id, current_date)
        
        # 如果沒有找到詞彙記錄，為用戶分配今日詞彙
        if not words:
            words = UserVocabulary.assign_daily_words(user_id, current_date)
            
        # 確保有返回結果
        if not words or len(words) == 0:
            # 使用備用詞彙
            fallback_words = [
                {'english': 'resilience', 'chinese': '彈性，適應力', 'difficulty': 3},
                {'english': 'endeavor', 'chinese': '努力，嘗試', 'difficulty': 3},
                {'english': 'persistence', 'chinese': '堅持，毅力', 'difficulty': 2}
            ]
            return fallback_words
            
        return words
    
    except Exception as e:
        print(f"獲取詞彙時出錯: {str(e)}")
        # 使用備用詞彙
        fallback_words = [
            {'english': 'resilience', 'chinese': '彈性，適應力', 'difficulty': 3},
            {'english': 'endeavor', 'chinese': '努力，嘗試', 'difficulty': 3},
            {'english': 'persistence', 'chinese': '堅持，毅力', 'difficulty': 2}
        ]
        return fallback_words


def format_daily_words(words):
    """
    格式化詞彙列表為顯示文本
    
    Args:
        words: 詞彙列表，每個詞彙包含english、chinese和difficulty屬性
        
    Returns:
        格式化後的文本
    """
    try:
        if not words or len(words) == 0:
            return "今日無學習詞彙。"
        
        formatted = "📚 今日單字學習\n\n"
        
        for i, word in enumerate(words, start=1):
            try:
                english = word.get('english', '未知')
                chinese = word.get('chinese', '未知')
                difficulty = min(int(word.get('difficulty', 2)), 5)
                stars = '⭐' * difficulty
                
                formatted += f"{i}. {english}\n"
                formatted += f"   {chinese}\n"
                formatted += f"   {stars}\n\n"
            except Exception as e:
                print(f"格式化單詞時出錯: {str(e)}")
                formatted += f"{i}. 格式化錯誤\n\n"
        
        return formatted
    except Exception as e:
        print(f"格式化單詞列表時出錯: {str(e)}")
        return "無法格式化詞彙列表，請稍後再試。"


def add_vocabulary(english, chinese, difficulty=2):
    """
    添加新詞彙到詞彙表
    
    Args:
        english: 英文單詞
        chinese: 中文翻譯
        difficulty: 難度等級(1-5)
        
    Returns:
        新增的詞彙ID
    """
    try:
        # 確保數據表存在
        Vocabulary.create_table_if_not_exists()
        
        # 添加詞彙
        word = Vocabulary.add_word(english, chinese, difficulty)
        return word['id'] if word else None
    
    except Exception as e:
        print(f"添加詞彙時出錯: {str(e)}")
        return None 