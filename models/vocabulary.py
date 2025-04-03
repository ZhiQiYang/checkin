"""
詞彙模型，對應數據庫中的vocabulary和user_vocabulary表
"""

import random
from datetime import datetime
from models.base import Model, Database

# 預設詞彙列表，用於初始化詞彙表
DEFAULT_VOCABULARY = [
    ("abundant", "豐富的", 2),
    ("accommodate", "容納；適應", 2),
    ("acquisition", "獲得；收購", 2),
    ("advocate", "提倡；擁護", 2),
    ("aesthetic", "美學的；審美的", 2),
    ("alleviate", "減輕；緩和", 2),
    ("ambiguous", "模糊的；不明確的", 2),
    ("ambitious", "有雄心的；野心勃勃的", 2),
    ("analogous", "類似的；相似的", 2),
    ("analyze", "分析；解析", 2),
    ("capricious", "反覆無常的；任性的", 3),
    ("clandestine", "秘密的；隱蔽的", 3),
    ("cognizant", "認識到的；意識到的", 3),
    ("connotation", "含義；內涵", 3),
    ("conundrum", "難題；謎語", 3),
    ("cryptic", "神秘的；含義隱晦的", 3),
    ("deference", "尊重；敬重", 3),
    ("deliberate", "深思熟慮的；故意的", 3),
    ("deleterious", "有害的；有毒的", 3),
    ("demystify", "揭秘；使明白易懂", 3),
    ("resilience", "恢復力；彈性", 4),
    ("endeavor", "努力；嘗試", 4),
    ("persistence", "堅持；毅力", 4),
]

class Vocabulary(Model):
    """詞彙模型類"""
    
    table_name = "vocabulary"
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "english_word": "TEXT UNIQUE NOT NULL",
        "chinese_translation": "TEXT NOT NULL",
        "difficulty": "INTEGER DEFAULT 2",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP"
    }
    
    @classmethod
    def get_by_id(cls, id_value):
        """通過ID獲取詞彙"""
        result = cls.find_by_id(id_value)
        return cls._row_to_dict(result) if result else None
    
    @classmethod
    def get_by_word(cls, word):
        """通過單詞獲取詞彙"""
        query = f"SELECT * FROM {cls.table_name} WHERE english_word = ?"
        result = Database.execute_query(query, (word,), 'one')
        return cls._row_to_dict(result) if result else None
    
    @classmethod
    def get_random_words(cls, count=3, difficulty=None):
        """獲取隨機詞彙"""
        conditions = None
        params = None
        
        if difficulty:
            conditions = "difficulty = ?"
            params = (difficulty,)
            
        query = f"SELECT * FROM {cls.table_name}"
        if conditions:
            query += f" WHERE {conditions}"
        query += f" ORDER BY RANDOM() LIMIT {count}"
        
        results = Database.execute_query(query, params, 'all')
        return [cls._row_to_dict(row) for row in results] if results else []
    
    @classmethod
    def add_word(cls, english, chinese, difficulty=2):
        """添加新詞彙"""
        # 檢查詞彙是否已存在
        existing_word = cls.get_by_word(english)
        if existing_word:
            return existing_word
            
        # 添加新詞彙
        data = {
            'english_word': english,
            'chinese_translation': chinese,
            'difficulty': difficulty
        }
        
        word_id = cls.insert(data)
        return cls.get_by_id(word_id)
    
    @staticmethod
    def _row_to_dict(row):
        """將數據庫結果轉換為字典"""
        if not row:
            return None
            
        columns = ['id', 'english_word', 'chinese_translation', 'difficulty', 'created_at']
        return {columns[i]: row[i] for i in range(len(columns)) if i < len(row)}


class UserVocabulary(Model):
    """用戶詞彙模型類，記錄用戶每日學習的詞彙"""
    
    table_name = "user_vocabulary"
    columns = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "user_id": "TEXT NOT NULL",
        "date": "TEXT NOT NULL",
        "word_ids": "TEXT NOT NULL",
        "created_at": "DATETIME DEFAULT CURRENT_TIMESTAMP",
        "UNIQUE": "(user_id, date)"
    }
    
    @classmethod
    def get_user_daily_words(cls, user_id, date):
        """獲取用戶某日的詞彙學習記錄"""
        query = f"SELECT * FROM {cls.table_name} WHERE user_id = ? AND date = ?"
        result = Database.execute_query(query, (user_id, date), 'one')
        if not result:
            return None
            
        # 解析word_ids
        user_vocab = cls._row_to_dict(result)
        if not user_vocab:
            return None
            
        word_ids = user_vocab['word_ids'].split(',')
        
        # 獲取詞彙詳情
        words = []
        for word_id in word_ids:
            word = Vocabulary.get_by_id(word_id)
            if word:
                words.append({
                    'english': word['english_word'],
                    'chinese': word['chinese_translation'],
                    'difficulty': word['difficulty']
                })
                
        return words
    
    @classmethod
    def assign_daily_words(cls, user_id, date, count=3):
        """為用戶分配每日詞彙"""
        # 檢查是否已有記錄
        existing = cls.get_user_daily_words(user_id, date)
        if existing:
            return existing
            
        # 獲取隨機詞彙
        random_words = Vocabulary.get_random_words(count)
        if not random_words:
            return []
            
        # 保存用戶詞彙記錄
        word_ids = [str(word['id']) for word in random_words]
        data = {
            'user_id': user_id,
            'date': date,
            'word_ids': ','.join(word_ids)
        }
        
        cls.insert(data)
        
        # 轉換為前端格式
        return [{
            'english': word['english_word'],
            'chinese': word['chinese_translation'],
            'difficulty': word['difficulty']
        } for word in random_words]
    
    @staticmethod
    def _row_to_dict(row):
        """將數據庫結果轉換為字典"""
        if not row:
            return None
            
        columns = ['id', 'user_id', 'date', 'word_ids', 'created_at']
        return {columns[i]: row[i] for i in range(len(columns)) if i < len(row)} 