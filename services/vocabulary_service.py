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
    
<<<<<<< HEAD
    Args:
        user_id: LINE用戶ID，如果為None則返回隨機詞彙
        
    Returns:
        包含詞彙信息的列表，每個詞彙包含英文、中文和難度
    """
    try:
        # 獲取當前日期
        current_date = datetime.now().strftime('%Y-%m-%d')
=======
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

def find_db_path():
    """查找並返回可用的數據庫文件路徑"""
    # 首先嘗試配置中的路徑
    db_path = Config.DB_PATH
    print(f"🔍 嘗試查找數據庫: {db_path}")
    
    if os.path.exists(db_path):
        print(f"✅ 使用配置的數據庫路徑: {db_path}")
        return db_path
        
    # 配置路徑不存在，嘗試其他可能的位置
    alt_paths = ['checkin.db', os.path.join('db', 'checkin.db')]
    for alt_path in alt_paths:
        if os.path.exists(alt_path):
            print(f"✅ 找到替代數據庫: {alt_path}")
            return alt_path
    
    # 如果無法找到現有數據庫，返回默認路徑作為新數據庫的位置
    print(f"⚠️ 無法找到現有數據庫，將使用配置路徑創建新數據庫: {db_path}")
    
    # 確保包含數據庫文件的目錄存在
    db_dir = os.path.dirname(db_path)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir)
            print(f"✅ 創建數據庫目錄: {db_dir}")
        except Exception as e:
            print(f"❌ 無法創建數據庫目錄: {e}")
    
    return db_path

def init_vocabulary_database():
    """初始化詞彙數據庫，如果表不存在則創建並插入預設詞彙"""
    try:
        # 使用統一的數據庫路徑查找函數
        db_path = find_db_path()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
>>>>>>> b244abde304f7e5306049e61768aeb382a52b33a
        
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
        
<<<<<<< HEAD
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
=======
        # 檢查用戶詞彙表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_vocabulary'")
        user_table_exists = cursor.fetchone() is not None
        
        if not user_table_exists:
            # 創建用戶詞彙關聯表
            cursor.execute('''
                CREATE TABLE user_vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    date TEXT NOT NULL,
                    word_ids TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, date)
                )
            ''')
            print("✅ 已創建用戶詞彙關聯表")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 初始化詞彙數據庫時出錯: {e}")
        if conn:
            conn.close()

def get_daily_words(date=None, user_id=None):
    """獲取三個英文單詞，無論環境如何都能可靠返回結果"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    # 預設備用詞彙，確保即使所有方法失敗也能返回詞彙
    fallback_words = [
        {'english': 'resilience', 'chinese': '恢復力；適應力', 'difficulty': 2},
        {'english': 'endeavor', 'chinese': '努力；嘗試', 'difficulty': 2},
        {'english': 'persistence', 'chinese': '堅持；毅力', 'difficulty': 2}
    ]
    
    # 如果沒有提供用戶ID，直接返回備用詞彙
    if not user_id:
        print("❌ 未提供用戶ID，返回備用詞彙")
        return fallback_words
    
    try:
        # 使用統一的數據庫路徑查找函數
        db_path = find_db_path()
        
        # 嘗試連接數據庫
        try:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            print(f"✅ 成功連接數據庫: {db_path}")
        except Exception as e:
            print(f"❌ 數據庫連接錯誤: {e}")
            return fallback_words
        
        # 確保user_vocabulary表存在
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_vocabulary'")
            if not cursor.fetchone():
                # 創建表
                cursor.execute('''
                    CREATE TABLE user_vocabulary (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id TEXT NOT NULL,
                        date TEXT NOT NULL,
                        word_ids TEXT NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id, date)
                    )
                ''')
                conn.commit()
                print("✅ 已創建user_vocabulary表")
        except Exception as e:
            print(f"❌ 檢查/創建user_vocabulary表失敗: {e}")
            # 繼續執行，不要中斷
        
        # 首先嘗試從用戶記錄獲取詞彙
        try:
            cursor.execute("SELECT * FROM user_vocabulary WHERE user_id = ? AND date = ?", (user_id, date))
            user_record = cursor.fetchone()
            
            if user_record:
                # 獲取詞彙ID
                try:
                    word_ids = user_record['word_ids'].split(',')
                except:
                    try:
                        # 嘗試通過索引獲取
                        word_ids = str(user_record[3]).split(',')
                    except:
                        print("❌ 無法解析word_ids")
                        return fallback_words
                
                # 獲取詞彙詳情
                words = []
                for word_id in word_ids:
                    try:
                        cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
                        word = cursor.fetchone()
                        if word:
                            try:
                                # 嘗試使用字典方式訪問
                                english = word['english_word']
                                chinese = word['chinese_translation']
                                difficulty = word['difficulty']
                            except:
                                try:
                                    # 嘗試使用索引方式訪問
                                    english = word[1]
                                    chinese = word[2]
                                    difficulty = word[3]
                                except:
                                    print(f"❌ 無法解析詞彙 ID {word_id}")
                                    continue
                            
                            words.append({
                                'english': english,
                                'chinese': chinese,
                                'difficulty': difficulty
                            })
                    except Exception as e:
                        print(f"❌ 獲取詞彙 ID {word_id} 出錯: {e}")
                
                # 如果成功獲取了詞彙，返回
                if len(words) > 0:
                    conn.close()
                    return words
            
            # 如果沒有找到用戶記錄或詞彙為空，創建新記錄
            # 簡化：直接獲取3個隨機詞彙
            cursor.execute("SELECT * FROM vocabulary ORDER BY RANDOM() LIMIT 3")
            vocab_records = cursor.fetchall()
            
            if vocab_records and len(vocab_records) > 0:
                words = []
                selected_ids = []
                
                for record in vocab_records:
                    try:
                        # 嘗試使用字典方式訪問
                        id = record['id']
                        english = record['english_word']
                        chinese = record['chinese_translation']
                        difficulty = record['difficulty']
                    except:
                        try:
                            # 嘗試使用索引方式訪問
                            id = record[0]
                            english = record[1]
                            chinese = record[2]
                            difficulty = record[3]
                        except:
                            continue
                    
                    words.append({
                        'english': english,
                        'chinese': chinese,
                        'difficulty': difficulty
                    })
                    selected_ids.append(str(id))
                
                # 如果成功獲取了詞彙
                if len(words) > 0:
                    # 嘗試保存用戶今日詞彙記錄，但不中斷流程
                    try:
                        cursor.execute(
                            "INSERT OR REPLACE INTO user_vocabulary (user_id, date, word_ids) VALUES (?, ?, ?)",
                            (user_id, date, ','.join(selected_ids))
                        )
                        conn.commit()
                    except Exception as e:
                        print(f"❌ 保存用戶詞彙記錄失敗: {e}")
                    
                    conn.close()
                    return words
        except Exception as e:
            print(f"❌ 獲取用戶詞彙記錄時出錯: {e}")
            # 繼續嘗試其他方法
        
        # 如果以上方法都失敗，嘗試直接獲取詞彙
        try:
            cursor.execute("SELECT english_word, chinese_translation, difficulty FROM vocabulary ORDER BY RANDOM() LIMIT 3")
            random_words = cursor.fetchall()
            
            if random_words and len(random_words) > 0:
                words = []
                for word in random_words:
                    try:
                        english = word[0] if isinstance(word, tuple) else word['english_word']
                        chinese = word[1] if isinstance(word, tuple) else word['chinese_translation']
                        difficulty = word[2] if isinstance(word, tuple) else word['difficulty']
                        
                        words.append({
                            'english': english,
                            'chinese': chinese,
                            'difficulty': difficulty
                        })
                    except:
                        continue
                
                if len(words) > 0:
                    return words
        except Exception as e:
            print(f"❌ 獲取隨機詞彙失敗: {e}")
        
        # 如果連接已打開，關閉它
        if 'conn' in locals() and conn:
            conn.close()
    
    except Exception as e:
        print(f"❌ 獲取每日單詞時出錯: {e}")
        # 使用備用詞彙
    
    # 如果所有嘗試都失敗，返回備用詞彙
    return fallback_words

def format_daily_words(words):
    """格式化每日單詞為回覆消息，確保即使words數據有問題也能返回結果"""
    if not words or len(words) == 0:
        return "📚 今日單字學習\n無法獲取單字，請稍後再試"
    
    try:
        message = "📚 今日單字學習\n"
        
        for i, word in enumerate(words, 1):
            try:
                # 獲取必要字段，設置默認值
                english = word.get('english', '未知詞彙')
                chinese = word.get('chinese', '未知翻譯')
                difficulty = word.get('difficulty', 2)
                
                # 確保difficulty是數字
                if not isinstance(difficulty, int):
                    try:
                        difficulty = int(difficulty)
                    except:
                        difficulty = 2
                
                # 限制最大難度為5星
                difficulty = min(difficulty, 5)
                
                difficulty_stars = "⭐" * difficulty
                message += f"{i}. {english} - {chinese} {difficulty_stars}\n"
            except Exception as e:
                print(f"格式化單詞 #{i} 失敗: {e}")
                message += f"{i}. 單詞數據格式錯誤\n"
        
        return message.strip()
    except Exception as e:
        print(f"格式化單詞列表失敗: {e}")
        # 如果格式化整個列表失敗，返回基本訊息
        return "📚 今日單字學習\n系統暫時無法正確顯示單字，但您今日的學習已記錄"

def add_vocabulary_word(english, chinese, difficulty=2):
    """添加新單詞到詞彙庫"""
    try:
        # 使用統一的數據庫路徑查找函數
        db_path = find_db_path()
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
>>>>>>> b244abde304f7e5306049e61768aeb382a52b33a
        
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
<<<<<<< HEAD
        print(f"添加詞彙時出錯: {str(e)}")
        return None 
=======
        print(f"❌ 添加詞彙時出錯: {e}")
        if conn:
            conn.close()
        return False 
>>>>>>> b244abde304f7e5306049e61768aeb382a52b33a
