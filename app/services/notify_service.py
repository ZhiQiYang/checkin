def handle_event(event):
    if event['type'] == 'message':
        text = event['message']['text']
        # 判斷 message 處理
