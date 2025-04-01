import sqlite3
import os
import random
from datetime import datetime, timedelta
from config import Config

# 更新為較高難度的詞彙庫，包含單詞、中文翻譯和難度級別（1-基礎, 2-中級, 3-高級）
DEFAULT_VOCABULARY = [
    # 中級詞彙 (難度2)
    ("abundant", "豐富的", 2),
    ("accommodate", "容納；適應", 2),
    ("acquisition", "獲得；收購", 2),
    ("advocate", "提倡；擁護", 2),
    ("aesthetic", "美學的；審美的", 2),
    ("aggravate", "加重；惡化", 2),
    ("alleviate", "減輕；緩和", 2),
    ("ambiguous", "模糊的；不明確的", 2),
    ("ambitious", "有雄心的；野心勃勃的", 2),
    ("analogous", "類似的；相似的", 2),
    ("analyze", "分析；解析", 2),
    ("anomaly", "異常；反常", 2),
    ("anticipate", "預期；預料", 2),
    ("apathy", "冷漠；無興趣", 2),
    ("apparatus", "儀器；裝置", 2),
    ("apparent", "明顯的；表面上的", 2),
    ("apprehensive", "憂慮的；擔心的", 2),
    ("articulate", "清晰表達的；發音清晰的", 2),
    ("assertion", "斷言；聲明", 2),
    ("assess", "評估；評價", 2),
    ("assimilate", "同化；吸收", 2),
    ("assumption", "假設；假定", 2),
    ("attain", "達到；獲得", 2),
    ("attribute", "屬性；特質", 2),
    ("augment", "增加；擴大", 2),
    ("authentic", "真實的；可靠的", 2),
    ("autonomy", "自主；自治", 2),
    ("bias", "偏見；偏向", 2),
    ("brevity", "簡潔；簡短", 2),
    ("catalyst", "催化劑；促進因素", 2),
    
    # 高級詞彙 (難度3)
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
    ("dichotomy", "二分法；對立", 3),
    ("didactic", "教導的；說教的", 3),
    ("disparate", "迥然不同的；不同類的", 3),
    ("dogmatic", "教條的；武斷的", 3),
    ("egregious", "極其惡劣的；過分的", 3),
    ("eloquent", "雄辯的；有說服力的", 3),
    ("empathy", "同理心；共情", 3),
    ("empirical", "實證的；經驗的", 3),
    ("ephemeral", "短暫的；瞬息的", 3),
    ("esoteric", "深奧的；只有內行才懂的", 3),
    ("euphemism", "委婉語；婉言", 3),
    ("exacerbate", "加劇；惡化", 3),
    ("exemplify", "例證；作為...的典型", 3),
    ("exorbitant", "過高的；過分的", 3),
    ("expedite", "加快；促進", 3),
    ("facetious", "愛開玩笑的；不嚴肅的", 3),
    ("fallacy", "謬論；錯誤觀念", 3),
    ("fastidious", "挑剔的；過分講究的", 3),
    ("fathom", "理解；測量深度", 3),
    ("fervent", "熱情的；熱烈的", 3),
]

def init_vocabulary_database():
    """初始化詞彙數據庫，如果表不存在則創建並插入預設詞彙"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        # 檢查詞彙表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vocabulary'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            # 創建詞彙表
            cursor.execute('''
                CREATE TABLE vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    english_word TEXT UNIQUE NOT NULL,
                    chinese_translation TEXT NOT NULL,
                    difficulty INTEGER DEFAULT 2,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 創建已使用詞彙記錄表
            cursor.execute('''
                CREATE TABLE word_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    word_ids TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 插入預設詞彙
            for word_data in DEFAULT_VOCABULARY:
                if len(word_data) == 3:
                    word, translation, difficulty = word_data
                    cursor.execute(
                        "INSERT INTO vocabulary (english_word, chinese_translation, difficulty) VALUES (?, ?, ?)",
                        (word, translation, difficulty)
                    )
                else:
                    word, translation = word_data
                    cursor.execute(
                        "INSERT INTO vocabulary (english_word, chinese_translation) VALUES (?, ?)",
                        (word, translation)
                    )
            
            conn.commit()
            print(f"✅ 已初始化詞彙數據庫，插入了 {len(DEFAULT_VOCABULARY)} 個預設單詞")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 初始化詞彙數據庫時出錯: {e}")
        if conn:
            conn.close()

def get_daily_words(date=None, user_id=None):
    """获取指定日期和用户的三个英文单词，如果该日期没有记录则创建新记录"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 检查词汇表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vocabulary'")
        if not cursor.fetchone():
            print("词汇表不存在，创建表...")
            init_vocabulary_database()
        
        # 检查今天是否已有单词记录
        if user_id:
            # 如果提供了用户ID，检查用户词汇表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_vocabulary'")
            if cursor.fetchone():
                cursor.execute("SELECT * FROM user_vocabulary WHERE user_id = ? AND date = ?", (user_id, date))
                user_record = cursor.fetchone()
                if user_record:
                    word_ids = user_record['word_ids'].split(',')
                    words = []
                    for word_id in word_ids:
                        cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
                        word = cursor.fetchone()
                        if word:
                            words.append({
                                'english': word['english_word'],
                                'chinese': word['chinese_translation'],
                                'difficulty': word['difficulty']
                            })
                    conn.close()
                    return words
        
        # 检查一般单词记录
        cursor.execute("SELECT * FROM word_usage WHERE date = ?", (date,))
        usage_record = cursor.fetchone()
        
        if usage_record:
            # 如果有记录，返回已选单词
            word_ids = usage_record['word_ids'].split(',')
            words = []
            
            for word_id in word_ids:
                cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
                word = cursor.fetchone()
                if word:
                    words.append({
                        'english': word['english_word'],
                        'chinese': word['chinese_translation'],
                        'difficulty': word['difficulty']
                    })
            
            conn.close()
            return words
        else:
            # 如果没有记录，选择三个新单词
            cursor.execute("SELECT id FROM vocabulary")
            all_ids = [row['id'] for row in cursor.fetchall()]
            
            if len(all_ids) < 3:
                print("词汇数量不足3个，无法生成每日单词")
                conn.close()
                return []
            
            # 随机选择3个单词
            selected_ids = random.sample(all_ids, 3)
            
            # 保存今天的单词使用记录
            cursor.execute(
                "INSERT INTO word_usage (date, word_ids) VALUES (?, ?)",
                (date, ','.join(map(str, selected_ids)))
            )
            
            # 获取选中单词的详细信息
            words = []
            for word_id in selected_ids:
                cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
                word = cursor.fetchone()
                if word:
                    words.append({
                        'english': word['english_word'],
                        'chinese': word['chinese_translation'],
                        'difficulty': word['difficulty']
                    })
            
            conn.commit()
            conn.close()
            return words
    
    except Exception as e:
        print(f"❌ 获取每日单词时出错: {e}")
        if 'conn' in locals() and conn:
            conn.close()
        return []

def format_daily_words(words):
    """格式化每日單詞為回覆消息"""
    if not words or len(words) == 0:
        return "📚 今日單字學習\n無法獲取單字，請稍後再試"
    
    message = "📚 今日單字學習\n"
    for i, word in enumerate(words, 1):
        difficulty_stars = "⭐" * word.get('difficulty', 2)  # 根據難度顯示星級
        message += f"{i}. {word['english']} - {word['chinese']} {difficulty_stars}\n"
    
    return message.strip()

def add_vocabulary_word(english, chinese, difficulty=2):
    """添加新單詞到詞彙庫"""
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO vocabulary (english_word, chinese_translation, difficulty) VALUES (?, ?, ?)",
            (english, chinese, difficulty)
        )
        
        conn.commit()
        conn.close()
        return True
    
    except Exception as e:
        print(f"❌ 添加詞彙時出錯: {e}")
        if conn:
            conn.close()
        return False 
