"""
數據庫初始化工具，用於創建所有必要的表格和默認數據
"""

import sys
import os

# 添加項目根目錄到系統路徑
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    Database, Model, User, CheckinRecord, 
    Vocabulary, UserVocabulary, ReminderSetting
)

DEFAULT_VOCABULARY = [
    # 中級詞彙 (難度2)
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
]

def init_database():
    """初始化所有數據庫表"""
    tables = [User, CheckinRecord, Vocabulary, UserVocabulary, ReminderSetting]
    
    print("開始初始化數據庫...")
    
    for table_model in tables:
        try:
            table_model.create_table_if_not_exists()
            print(f"✅ 表 {table_model.table_name} 已創建或已存在")
        except Exception as e:
            print(f"❌ 創建表 {table_model.table_name} 時出錯: {str(e)}")

def init_vocabulary():
    """初始化詞彙表"""
    try:
        # 確保表存在
        Vocabulary.create_table_if_not_exists()
        
        # 查詢表中的詞彙數量
        query = f"SELECT COUNT(*) FROM {Vocabulary.table_name}"
        result = Database.execute_query(query, None, 'one')
        word_count = result[0] if result else 0
        
        # 如果表為空，添加默認詞彙
        if word_count == 0:
            print(f"詞彙表為空，添加 {len(DEFAULT_VOCABULARY)} 個默認詞彙...")
            
            for english, chinese, difficulty in DEFAULT_VOCABULARY:
                Vocabulary.add_word(english, chinese, difficulty)
                
            print("✅ 默認詞彙已添加")
        else:
            print(f"詞彙表已有 {word_count} 個單詞，跳過初始化")
            
    except Exception as e:
        print(f"❌ 初始化詞彙表時出錯: {str(e)}")

if __name__ == "__main__":
    # 初始化所有表
    init_database()
    
    # 初始化詞彙
    init_vocabulary()
    
    print("數據庫初始化完成") 