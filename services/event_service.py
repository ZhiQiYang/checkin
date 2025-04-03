import logging
import traceback
from services.notification_service import send_reply
from services.group_service import save_group_message
from services.command_service import CommandService

logger = logging.getLogger(__name__)

class EventService:
    """處理LINE Webhook事件的服務類"""
    
    @staticmethod
    def process_events(events):
        """處理多個事件"""
        results = []
        
        for event in events:
            try:
                result = EventService.process_event(event)
                results.append(result)
            except Exception as e:
                logger.error(f"處理事件出錯: {str(e)}")
                logger.debug(traceback.format_exc())
                results.append({"status": "error", "message": str(e)})
                
        return results
    
    @staticmethod
    def process_event(event):
        """處理單個事件，區分不同類型的事件"""
        event_type = event.get('type')
        
        # 根據事件類型處理
        if event_type == 'message':
            return EventService.process_message_event(event)
        elif event_type == 'follow':
            return EventService.process_follow_event(event)
        elif event_type == 'unfollow':
            return EventService.process_unfollow_event(event)
        elif event_type == 'join':
            return EventService.process_join_event(event)
        elif event_type == 'leave':
            return EventService.process_leave_event(event)
        elif event_type == 'postback':
            return EventService.process_postback_event(event)
        else:
            logger.warning(f"未處理的事件類型: {event_type}")
            return {"status": "ignored", "type": event_type}
    
    @staticmethod
    def process_message_event(event):
        """處理消息事件"""
        message = event.get('message', {})
        message_type = message.get('type')
        reply_token = event.get('replyToken')
        source_type = event.get('source', {}).get('type')
        
        # 保存群組消息
        if source_type == 'group' and message_type == 'text':
            group_id = event['source'].get('groupId')
            user_id = event['source'].get('userId', 'unknown')
            text = message.get('text', '')
            try:
                save_group_message(group_id, user_id, text)
            except Exception as e:
                logger.error(f"保存群組消息失敗: {str(e)}")
        
        # 處理文本消息
        if message_type == 'text' and reply_token:
            text = message.get('text', '')
            
            # 使用命令服務處理命令
            result = CommandService.handle_command(event, text)
            if result:
                return {"status": "success", "message": "command_handled"}
                
            # 如果不是命令或命令未處理，可以在這裡處理其他消息邏輯
            
            # 處理其他文本消息（如閒聊、AI回應等）
            # ...
            
        # 處理其他類型的消息（圖片、位置等）
        elif message_type == 'image':
            # 處理圖片消息
            # ...
            pass
        elif message_type == 'location':
            # 處理位置消息
            # ...
            pass
        
        return {"status": "success", "type": "message", "message_type": message_type}
    
    @staticmethod
    def process_follow_event(event):
        """處理追蹤事件（用戶添加好友）"""
        reply_token = event.get('replyToken')
        user_id = event.get('source', {}).get('userId')
        
        if reply_token and user_id:
            welcome_message = (
                "👋 感謝您加入打卡系統！\n\n"
                "您可以使用以下指令：\n"
                "!上班打卡 - 完成上班打卡\n"
                "!下班打卡 - 完成下班打卡\n"
                "!幫助 - 查看所有指令列表\n\n"
                "祝您使用愉快！"
            )
            send_reply(reply_token, welcome_message)
            
            # 這裡可以添加其他邏輯，例如記錄新用戶、設置默認提醒等
            
        return {"status": "success", "type": "follow", "user_id": user_id}
    
    @staticmethod
    def process_unfollow_event(event):
        """處理取消追蹤事件（用戶刪除好友）"""
        user_id = event.get('source', {}).get('userId')
        
        # 這裡可以添加用戶取消追蹤的處理邏輯
        # 例如禁用該用戶的提醒、標記帳號為非活躍等
        
        return {"status": "success", "type": "unfollow", "user_id": user_id}
    
    @staticmethod
    def process_join_event(event):
        """處理加入群組事件"""
        reply_token = event.get('replyToken')
        group_id = event.get('source', {}).get('groupId')
        
        if reply_token and group_id:
            welcome_message = (
                "👋 感謝您邀請打卡系統加入群組！\n\n"
                "群組成員可以使用以下指令：\n"
                "!上班打卡 - 完成上班打卡\n"
                "!下班打卡 - 完成下班打卡\n"
                "!幫助 - 查看所有指令列表\n\n"
                "祝大家使用愉快！"
            )
            send_reply(reply_token, welcome_message)
            
            # 這裡可以添加其他邏輯，例如記錄新群組等
            
        return {"status": "success", "type": "join", "group_id": group_id}
    
    @staticmethod
    def process_leave_event(event):
        """處理離開群組事件"""
        group_id = event.get('source', {}).get('groupId')
        
        # 這裡可以添加機器人離開群組的處理邏輯
        # 例如標記群組為非活躍等
        
        return {"status": "success", "type": "leave", "group_id": group_id}
    
    @staticmethod
    def process_postback_event(event):
        """處理postback事件（用戶點擊按鈕等）"""
        reply_token = event.get('replyToken')
        user_id = event.get('source', {}).get('userId')
        postback_data = event.get('postback', {}).get('data', '')
        
        # 根據postback數據處理不同的操作
        if postback_data.startswith('action=checkin'):
            # 處理打卡動作
            # ...
            pass
        elif postback_data.startswith('action=reminder'):
            # 處理提醒設置
            # ...
            pass
        
        return {"status": "success", "type": "postback", "data": postback_data} 