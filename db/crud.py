# db/crud.py
import sqlite3
from datetime import datetime
from contextlib import contextmanager
from config import Config
from utils.timezone import get_date_string

# 數據庫路徑
DB_PATH = Config.DB_PATH

@contextmanager
def get_db_connection(row_factory=sqlite3.Row):
    """
    創建一個上下文管理器，確保數據庫連接在使用後正確關閉
    
    Args:
        row_factory: 行工廠，預設為 sqlite3.Row 返回類似字典的結果
        
    Yields:
        sqlite3.Connection: 數據庫連接對象
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = row_factory
        yield conn
    finally:
        if conn is not None:
            conn.close()

def init_db():
    """初始化資料庫，如果表不存在則創建"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # 檢查表是否已存在
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [table[0] for table in c.fetchall()]
        
        # 建立打卡紀錄表格（如果不存在）
        if 'checkin_records' not in existing_tables:
            c.execute('''
                CREATE TABLE IF NOT EXISTS checkin_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    location TEXT,
                    note TEXT,
                    latitude REAL,
                    longitude REAL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    checkin_type TEXT DEFAULT '上班'
                )
            ''')
            print("✅ 創建了 checkin_records 表")
        
        # 建立群組訊息表格（如果不存在）
        if 'group_messages' not in existing_tables:
            c.execute('''
                CREATE TABLE IF NOT EXISTS group_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    user_name TEXT NOT NULL,
                    message TEXT,
                    timestamp TEXT NOT NULL
                )
            ''')
            print("✅ 創建了 group_messages 表")
        
        # 建立用戶表（如果不存在）
        if 'users' not in existing_tables:
            c.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    display_name TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            print("✅ 創建了 users 表")
        
        # 建立提醒設置表（如果不存在）
        if 'reminder_settings' not in existing_tables or 'reminder_logs' not in existing_tables:
            create_reminder_tables()
        
        conn.commit()

def create_reminder_tables():
    """創建提醒相關的表格"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        # 提醒設置表
        c.execute('''
            CREATE TABLE IF NOT EXISTS reminder_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                morning_time TEXT DEFAULT '09:00',
                evening_time TEXT DEFAULT '18:00',
                weekend_enabled INTEGER DEFAULT 0,
                holiday_enabled INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME,
                UNIQUE(user_id)
            )
        ''')
        
        # 提醒日誌表
        c.execute('''
            CREATE TABLE IF NOT EXISTS reminder_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                reminder_type TEXT NOT NULL,
                sent_at DATETIME,
                status TEXT
            )
        ''')
        
        conn.commit()

def save_group_message(user_id, user_name, message, timestamp):
    """保存群組消息到數據庫"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            INSERT INTO group_messages (user_id, user_name, message, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (user_id, user_name, message, timestamp))
        conn.commit()

def get_recent_messages(count=20):
    """獲取最近的群組消息"""
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute('''
            SELECT * FROM group_messages 
            ORDER BY id DESC LIMIT ?
        ''', (count,))
        results = c.fetchall()
        
        # 轉換為字典列表
        messages = []
        for row in results:
            messages.append({
                "user_id": row["user_id"],
                "user_name": row["user_name"],
                "message": row["message"],
                "timestamp": row["timestamp"]
            })
        return messages

def save_or_update_user(user_id, name, display_name=None):
    """保存或更新用戶信息"""
    with get_db_connection() as conn:
        try:
            c = conn.cursor()
            
            # 檢查用戶是否已存在
            c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
            user = c.fetchone()
            
            if user:
                # 更新現有用戶
                c.execute('''
                    UPDATE users 
                    SET name = ?, display_name = COALESCE(?, display_name)
                    WHERE user_id = ?
                ''', (name, display_name, user_id))
            else:
                # 新增用戶
                c.execute('''
                    INSERT INTO users (user_id, name, display_name)
                    VALUES (?, ?, ?)
                ''', (user_id, name, display_name))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"保存或更新用戶時出錯: {str(e)}")
            return False

def insert_checkin_record(user_id, name, location, note, latitude, longitude, date, time_str, checkin_type):
    """插入打卡記錄到數據庫"""
    with get_db_connection() as conn:
        try:
            c = conn.cursor()
            c.execute('''
                INSERT INTO checkin_records 
                (user_id, name, location, note, latitude, longitude, date, time, checkin_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, location, note, latitude, longitude, date, time_str, checkin_type))
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"插入打卡記錄時出錯: {str(e)}")
            return False

def has_checkin_today(user_id, checkin_type, date=None):
    """檢查用戶當天是否已有特定類型的打卡記錄"""
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
        
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute(
            'SELECT * FROM checkin_records WHERE user_id = ? AND date = ? AND checkin_type = ?', 
            (user_id, date, checkin_type)
        )
        return c.fetchone() is not None

def save_checkin(user_id, name, location, note=None, latitude=None, longitude=None, checkin_type="上班"):
    """保存打卡記錄到數據庫，確保打卡順序正確"""
    with get_db_connection() as conn:
        try:
            c = conn.cursor()

            # 取得今天日期
            today = get_date_string()
            
            # 先檢查是否已有相同類型的打卡記錄
            c.execute('SELECT * FROM checkin_records WHERE user_id = ? AND date = ? AND checkin_type = ?', 
                    (user_id, today, checkin_type))
            
            if c.fetchone():
                return False, f"今天已經{checkin_type}打卡過了"

            # 如果是下班打卡，檢查今天是否已經有上班打卡
            if checkin_type == "下班":
                c.execute('SELECT * FROM checkin_records WHERE user_id = ? AND date = ? AND checkin_type = ?', 
                        (user_id, today, "上班"))
                
                if not c.fetchone():
                    return False, "請先完成上班打卡，才能進行下班打卡"

            now = datetime.now()
            time_str = now.strftime('%H:%M:%S')

            # 插入新紀錄
            c.execute('''
                INSERT INTO checkin_records 
                (user_id, name, location, note, latitude, longitude, date, time, checkin_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, name, location, note, latitude, longitude, today, time_str, checkin_type))

            conn.commit()
            return True, f"{checkin_type}打卡成功"
        except Exception as e:
            conn.rollback()
            print(f"保存打卡記錄錯誤: {str(e)}")
            return False, f"數據庫錯誤: {str(e)}"

def get_reminder_setting(user_id):
    """獲取用戶的提醒設置"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        c.execute('SELECT * FROM reminder_settings WHERE user_id = ?', (user_id,))
        row = c.fetchone()
        
        if not row:
            # 默認設置
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute('''
                INSERT INTO reminder_settings 
                (user_id, created_at, updated_at) 
                VALUES (?, ?, ?)
            ''', (user_id, now, now))
            conn.commit()
            
            c.execute('SELECT * FROM reminder_settings WHERE user_id = ?', (user_id,))
            row = c.fetchone()
        
        setting = dict(row) if row else None
        return setting

def update_reminder_setting(user_id, settings):
    """更新用戶的提醒設置"""
    with get_db_connection() as conn:
        try:
            c = conn.cursor()
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            fields = []
            values = []
            
            for key, value in settings.items():
                if key in ['enabled', 'morning_time', 'evening_time', 
                          'weekend_enabled', 'holiday_enabled']:
                    fields.append(f"{key} = ?")
                    values.append(value)
            
            if not fields:
                return False
            
            fields.append("updated_at = ?")
            values.append(now)
            values.append(user_id)
            
            query = f'''
                UPDATE reminder_settings
                SET {", ".join(fields)}
                WHERE user_id = ?
            '''
            
            c.execute(query, values)
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"更新提醒設置時出錯: {str(e)}")
            return False

def log_reminder(user_id, reminder_type):
    """記錄已發送的提醒"""
    with get_db_connection() as conn:
        try:
            c = conn.cursor()
            
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            c.execute('''
                INSERT INTO reminder_logs
                (user_id, reminder_type, sent_at, status)
                VALUES (?, ?, ?, ?)
            ''', (user_id, reminder_type, now, 'sent'))
            
            conn.commit()
            return True
        except Exception as e:
            conn.rollback()
            print(f"記錄提醒時出錯: {str(e)}")
            return False

def get_users_needing_reminder(reminder_type):
    """獲取需要發送提醒的用戶列表"""
    with get_db_connection() as conn:
        c = conn.cursor()
        
        now = datetime.now()
        current_time = now.strftime('%H:%M')
        today = now.strftime('%Y-%m-%d')
        
        # 檢查是否為週末
        is_weekend = now.weekday() >= 5  # 5=Saturday, 6=Sunday
        
        # 獲取今天有特定類型提醒的用戶列表
        time_field = 'morning_time' if reminder_type == '上班' else 'evening_time'
        
        c.execute(f'''
            SELECT r.user_id, r.{time_field}, u.name, u.display_name
            FROM reminder_settings r
            JOIN users u ON r.user_id = u.user_id
            WHERE r.enabled = 1 
            AND r.{time_field} <= ?
            AND (r.weekend_enabled = 1 OR ? = 0)
        ''', (current_time, 1 if is_weekend else 0))
        
        potential_users = c.fetchall()
        users_to_remind = []
        
        for user in potential_users:
            # 檢查今天是否已經打卡
            c.execute('''
                SELECT * FROM checkin_records
                WHERE user_id = ? AND date = ? AND checkin_type = ?
            ''', (user['user_id'], today, reminder_type))
            
            if c.fetchone() is None:
                # 檢查今天是否已經發送過提醒
                c.execute('''
                    SELECT * FROM reminder_logs
                    WHERE user_id = ? AND reminder_type = ? AND DATE(sent_at) = ?
                ''', (user['user_id'], reminder_type, today))
                
                if c.fetchone() is None:
                    users_to_remind.append({
                        'user_id': user['user_id'],
                        'name': user['name'] or user['display_name'],
                        'reminder_time': user[time_field]
                    })
        
        return users_to_remind
