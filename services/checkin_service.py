from db.crud import save_checkin

def handle_checkin(data):
    user_id = data.get('userId')
    name = data.get('displayName')
    location = data.get('location', '未知地點')
    note = data.get('note')
    lat = data.get('latitude')
    lng = data.get('longitude')

    return save_checkin(user_id, name, location, note, lat, lng)
