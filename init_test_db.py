from db.crud import init_db, insert_checkin_record, save_or_update_user, save_group_message
from datetime import datetime

def initialize_test_data():
    # 初始化資料庫
    init_db()
    
    # 新增測試用戶
    test_users = [
        ("U123", "張三", "Zhang San"),
        ("U456", "李四", "Li Si"),
        ("U789", "王五", "Wang Wu")
    ]
    
    for user_id, name, display_name in test_users:
        save_or_update_user(user_id, name, display_name)
    
    # 新增測試打卡記錄
    today = datetime.now().strftime('%Y-%m-%d')
    time_str = datetime.now().strftime('%H:%M:%S')
    
    test_records = [
        ("U123", "張三", "台北市信義區", "正常上班", 25.033, 121.564, today, time_str, "上班"),
        ("U456", "李四", "台北市內湖區", "外勤", 25.082, 121.556, today, time_str, "上班"),
        ("U789", "王五", "新北市板橋區", "遠端工作", 25.013, 121.465, today, time_str, "上班")
    ]
    
    for record in test_records:
        insert_checkin_record(*record)
    
    # 新增測試群組訊息
    test_messages = [
        ("U123", "張三", "早安，我已經到公司了", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ("U456", "李四", "我今天在客戶端工作", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
        ("U789", "王五", "收到，我在家遠端工作", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    ]
    
    for message in test_messages:
        save_group_message(*message)

if __name__ == "__main__":
    initialize_test_data()
    print("測試資料初始化完成！") 