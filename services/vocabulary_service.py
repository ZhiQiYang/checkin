import sqlite3
import os
import random
from datetime import datetime, timedelta
from config import Config

# 預設單詞庫，包含單詞和中文翻譯（這只是一個起始集，實際應用中應該有更多單詞）
DEFAULT_VOCABULARY = [
    ("abandon", "放棄"),
    ("ability", "能力"),
    ("absence", "缺席"),
    ("absorb", "吸收"),
    ("abstract", "抽象的"),
    ("academic", "學術的"),
    ("accept", "接受"),
    ("access", "訪問"),
    ("accident", "事故"),
    ("accommodate", "容納"),
    ("accomplish", "完成"),
    ("account", "帳戶"),
    ("accurate", "精確的"),
    ("achieve", "達成"),
    ("acknowledge", "承認"),
    ("acquire", "獲得"),
    ("adapt", "適應"),
    ("add", "添加"),
    ("address", "地址"),
    ("adequate", "足夠的"),
    ("adjust", "調整"),
    ("administration", "管理"),
    ("admire", "欽佩"),
    ("admit", "承認"),
    ("adolescent", "青少年"),
    ("adopt", "採用"),
    ("advance", "前進"),
    ("advantage", "優勢"),
    ("adventure", "冒險"),
    ("advertise", "廣告"),
    ("advice", "建議"),
    ("affect", "影響"),
    ("afford", "負擔得起"),
    ("afraid", "害怕的"),
    ("afternoon", "下午"),
    ("again", "再次"),
    ("against", "反對"),
    ("age", "年齡"),
    ("agency", "機構"),
    ("agenda", "議程"),
    ("aggressive", "積極的"),
    ("agree", "同意"),
    ("agriculture", "農業"),
    ("ahead", "向前"),
    ("aid", "援助"),
    ("aim", "目標"),
    ("air", "空氣"),
    ("aircraft", "飛機"),
    ("airline", "航空公司"),
    ("airport", "機場"),
    # 在實際項目中可添加更多單詞...
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
                    difficulty INTEGER DEFAULT 1,
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
            for word, translation in DEFAULT_VOCABULARY:
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

def get_daily_words(date=None):
    """獲取指定日期的三個英文單詞，如果該日期沒有記錄則創建新記錄"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    try:
        conn = sqlite3.connect(Config.DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 檢查今天是否已有單詞記錄
        cursor.execute("SELECT * FROM word_usage WHERE date = ?", (date,))
        usage_record = cursor.fetchone()
        
        if usage_record:
            # 如果有記錄，返回已選單詞
            word_ids = usage_record['word_ids'].split(',')
            words = []
            
            for word_id in word_ids:
                cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
                word = cursor.fetchone()
                if word:
                    words.append({
                        'english': word['english_word'],
                        'chinese': word['chinese_translation']
                    })
            
            conn.close()
            return words
        else:
            # 如果沒有記錄，選擇三個新單詞
            # 獲取3年內（約1095天）已使用的單詞ID
            three_years_ago = (datetime.now() - timedelta(days=1095)).strftime("%Y-%m-%d")
            cursor.execute("SELECT word_ids FROM word_usage WHERE date >= ?", (three_years_ago,))
            used_records = cursor.fetchall()
            
            used_ids = set()
            for record in used_records:
                used_ids.update(record['word_ids'].split(','))
            
            # 獲取所有單詞ID
            cursor.execute("SELECT id FROM vocabulary")
            all_ids = [row['id'] for row in cursor.fetchall()]
            
            # 排除已使用的單詞
            available_ids = [id for id in all_ids if str(id) not in used_ids]
            
            # 如果可用單詞不足，則重用最早使用的單詞
            if len(available_ids) < 3:
                print("可用單詞不足3個，重用最早的單詞")
                cursor.execute("SELECT word_ids FROM word_usage ORDER BY date LIMIT ?", 
                              (3 - len(available_ids),))
                oldest_records = cursor.fetchall()
                for record in oldest_records:
                    oldest_ids = record['word_ids'].split(',')
                    available_ids.extend([int(id) for id in oldest_ids])
            
            # 隨機選擇3個單詞
            selected_ids = random.sample(available_ids, 3)
            
            # 保存今天的單詞使用記錄
            cursor.execute(
                "INSERT INTO word_usage (date, word_ids) VALUES (?, ?)",
                (date, ','.join(map(str, selected_ids)))
            )
            
            # 獲取選中單詞的詳細信息
            words = []
            for word_id in selected_ids:
                cursor.execute("SELECT * FROM vocabulary WHERE id = ?", (word_id,))
                word = cursor.fetchone()
                if word:
                    words.append({
                        'english': word['english_word'],
                        'chinese': word['chinese_translation']
                    })
            
            conn.commit()
            conn.close()
            return words
    
    except Exception as e:
        print(f"❌ 獲取每日單詞時出錯: {e}")
        if conn:
            conn.close()
        return []

def format_daily_words(words):
    """格式化每日單詞為回覆消息"""
    if not words or len(words) == 0:
        return "📚 今日單字學習\n無法獲取單字，請稍後再試"
    
    message = "📚 今日單字學習\n"
    for i, word in enumerate(words, 1):
        message += f"{i}. {word['english']} - {word['chinese']}\n"
    
    return message.strip()

def add_vocabulary_word(english, chinese, difficulty=1):
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