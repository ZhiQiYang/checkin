# utils/validator.py
def validate_checkin_input(data):
    """驗證打卡輸入數據"""
    errors = []
    
    if not data.get('userId'):
        errors.append("缺少用戶ID")
    
    if not data.get('displayName'):
        errors.append("缺少用戶名稱")
    
    if not data.get('location'):
        errors.append("缺少位置信息")
        
    # 驗證經緯度（如果提供）
    try:
        if data.get('latitude'):
            float(data.get('latitude'))
        if data.get('longitude'):
            float(data.get('longitude'))
    except ValueError:
        errors.append("經緯度格式不正確")
        
    return errors
