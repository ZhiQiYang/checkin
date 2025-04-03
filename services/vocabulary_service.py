"""
詞彙服務：提供詞彙學習相關的功能
"""

import random
import sqlite3
import os
from datetime import datetime, timedelta
# 假設您的模型和配置是這樣導入的，如果不同請自行修改
from models import Vocabulary, UserVocabulary
# 假設您有一個 Config 模組或物件來儲存 DB_PATH
# from config import Config
# 如果沒有 Config，則需要直接定義 db_path 或修改 find_db_path
class Config: # 臨時替代 Config，您應該使用您自己的配置方式
    DB_PATH = 'checkin.db'


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
    """初始化詞彙數據庫，如果表不存在則創建，並添加默認詞彙"""
    try:
        # 確保數據表存在 (調用模型的方法)
        print("ℹ️ 正在檢查並確保詞彙相關數據表存在...")
        Vocabulary.create_table_if_not_exists()
        UserVocabulary.create_table_if_not_exists()
        print("✅ 詞彙數據表檢查/創建完成")
        
        # 檢查詞彙表是否為空，如果是則添加默認詞彙
        word_count = Vocabulary.count()
        print(f"DEBUG: 當前詞彙表數量: {word_count}")
        
        if word_count == 0:
            # 從 models.vocabulary 中導入預設詞彙
            from models.vocabulary import DEFAULT_VOCABULARY
            print(f"ℹ️ 詞彙表為空，添加 {len(DEFAULT_VOCABULARY)} 個默認詞彙...")
            
            added_count = 0
            skipped_count = 0
            for data_tuple in DEFAULT_VOCABULARY:
                # 解包時處理可能的長度不匹配
                if len(data_tuple) == 3:
                    english, chinese, difficulty = data_tuple
                elif len(data_tuple) == 2:
                    english, chinese = data_tuple
                    difficulty = 2  # 默認難度
                else:
                    print(f"⚠️ 跳過格式不符的預設詞彙: {data_tuple}")
                    skipped_count += 1
                    continue
                
                try:
                    # 使用模型方法添加詞彙
                    word = Vocabulary.add_word(english, chinese, difficulty)
                    if word:
                        added_count += 1
                except Exception as insert_error:
                    print(f"⚠️ 添加默認詞彙 '{english}' 時出錯: {insert_error}")
                    skipped_count += 1
            
            # 輸出結果統計
            final_count = Vocabulary.count()
            print(f"✅ 默認詞彙初始化完成。新增: {added_count}, 跳過: {skipped_count}, 總計: {final_count}")
        else:
            print(f"ℹ️ 詞彙表已有 {word_count} 個單詞，跳過默認詞彙初始化")
            
    except Exception as e:
        print(f"❌ 初始化詞彙數據庫時出錯: {e}")
        import traceback
        print(traceback.format_exc())  # 打印詳細錯誤追蹤


def get_daily_words(date=None, user_id=None):
    """獲取用戶當日的學習詞彙，無論環境如何都能可靠返回結果"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    # 預設備用詞彙，確保即使所有方法失敗也能返回詞彙
    fallback_words = [
        {'english': 'resilience', 'chinese': '恢復力；適應力', 'difficulty': 2},
        {'english': 'endeavor', 'chinese': '努力；嘗試', 'difficulty': 2},
        {'english': 'persistence', 'chinese': '堅持；毅力', 'difficulty': 2}
    ]

    # 如果沒有提供用戶ID，直接返回隨機詞彙 (修改：調用模型方法)
    if not user_id:
        print("ℹ️ 未提供用戶ID，返回隨機詞彙")
        try:
            # 確保數據表存在
            Vocabulary.create_table_if_not_exists()
            words_from_db = Vocabulary.get_random_words(count=3)
            if words_from_db:
                 return [{
                    'english': word['english_word'],
                    'chinese': word['chinese_translation'],
                    'difficulty': word['difficulty']
                 } for word in words_from_db]
            else:
                 return fallback_words
        except Exception as e:
            print(f"❌ 獲取隨機詞彙時出錯: {e}")
            return fallback_words

    # --- 以下是有 user_id 的邏輯 ---
    try:
        # 確保數據表存在 (雖然 init 做過，這裡再次確保)
        Vocabulary.create_table_if_not_exists()
        UserVocabulary.create_table_if_not_exists()

        # 查詢用戶今日詞彙 (使用模型方法)
        words = UserVocabulary.get_user_daily_words(user_id, date)

        # 如果沒有找到詞彙記錄，為用戶分配今日詞彙 (使用模型方法)
        if not words:
            print(f"ℹ️ 用戶 {user_id} 今日尚無詞彙，正在分配...")
            words = UserVocabulary.assign_daily_words(user_id, date)

        # 確保有返回結果
        if words and len(words) > 0:
             # 確保返回的是字典列表
            if isinstance(words[0], dict) and 'english' in words[0]:
                return words
            else:
                # 如果模型返回的不是期望格式，嘗試從 Vocabulary 獲取詳情
                # (這部分邏輯依賴於 UserVocabulary 返回的具體內容，可能需要調整)
                print(f"⚠️ UserVocabulary 返回格式不符，嘗試重新獲取詳情...")
                # 假設 words 是包含 word_id 的列表或元組列表
                detailed_words = []
                word_ids_to_fetch = []
                if isinstance(words[0], dict) and 'word_id' in words[0]:
                    word_ids_to_fetch = [w['word_id'] for w in words]
                elif isinstance(words[0], (int, str)): # 假設直接返回 ID 列表
                    word_ids_to_fetch = words
                # ... 其他可能的格式判斷

                if word_ids_to_fetch:
                    vocab_details = Vocabulary.get_words_by_ids(word_ids_to_fetch)
                    # 將 vocab_details 轉換回目標格式
                    for detail in vocab_details:
                         detailed_words.append({
                            'english': detail['english_word'],
                            'chinese': detail['chinese_translation'],
                            'difficulty': detail['difficulty']
                         })
                    if detailed_words:
                        return detailed_words

                print(f"❌ 無法轉換 UserVocabulary 返回結果，使用備用詞彙")
                return fallback_words


        # 如果分配後仍然沒有詞彙 (可能詞彙庫為空?)
        print(f"❌ 分配後仍然無法獲取用戶 {user_id} 的詞彙，使用備用詞彙")
        return fallback_words

    except Exception as e:
        print(f"❌ 獲取用戶 {user_id} 每日單詞時出錯: {e}")
        # 使用備用詞彙
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
                difficulty = word.get('difficulty', 2) # 預設難度

                # 確保difficulty是數字
                if not isinstance(difficulty, int):
                    try:
                        difficulty = int(difficulty)
                    except (ValueError, TypeError):
                        difficulty = 2 # 如果轉換失敗，使用預設值

                # 限制最大難度為5星
                difficulty = max(1, min(difficulty, 5)) # 確保至少1星，最多5星

                difficulty_stars = "⭐" * difficulty
                # message += f"{i}. {english} - {chinese} {difficulty_stars}\n" # 原來的格式
                # 修改為更清晰的格式
                message += f"\n{i}. {english}\n"
                message += f"   {chinese}\n"
                message += f"   難度: {difficulty_stars}\n"

            except Exception as e:
                print(f"格式化單詞 #{i} 失敗: {e}")
                message += f"\n{i}. 單詞數據格式錯誤\n"

        return message.strip()
    except Exception as e:
        print(f"格式化單詞列表失敗: {e}")
        # 如果格式化整個列表失敗，返回基本訊息
        return "📚 今日單字學習\n系統暫時無法正確顯示單字，但您今日的學習已記錄"

def add_vocabulary(english, chinese, difficulty=2):
    """
    添加新詞彙到詞彙表 (使用模型方法)

    Args:
        english: 英文單詞
        chinese: 中文翻譯
        difficulty: 難度等級(1-5)

    Returns:
        新增的詞彙ID，如果失敗則返回 None
    """
    try:
        # 確保數據表存在
        Vocabulary.create_table_if_not_exists()

        # 添加詞彙 (調用模型的方法)
        word = Vocabulary.add_word(english, chinese, difficulty)
        if word and 'id' in word:
            print(f"✅ 成功添加詞彙: {english} (ID: {word['id']})")
            return word['id']
        else:
             # 如果 add_word 失敗或返回格式不對
             print(f"❌ 添加詞彙 '{english}' 後無法獲取 ID，可能已存在或返回格式錯誤")
             # 嘗試再次查詢以獲取 ID (如果詞彙已存在)
             existing_word = Vocabulary.get_by_word(english)
             if existing_word and 'id' in existing_word:
                 return existing_word['id']
             return None

    except Exception as e:
        # 使用 logging 記錄錯誤會更好
        print(f"❌ 添加詞彙 '{english}' 時出錯: {e}")
        import traceback
        print(traceback.format_exc()) # 打印詳細錯誤
        return None
