import json
from channels.auth import AuthMiddlewareStack
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
from .models import Message, Group

logger = logging.getLogger(__name__)

class ChatConsumer(AsyncWebsocketConsumer):
    
    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.user = self.scope["user"]
        self.room_group_name = f"chat_{self.room_name}"
        
        
        if not self.scope["user"].is_authenticated:
            logger.exception("User not authecatited")
            self.close()
            return 
        
        logger.info("User authecatited")
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
  
        

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        if not self.scope["user"].is_authenticated:
            logger.exception("User not authecatited")
            self.close()
            return
        
        logger.info("User authecatited")
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", 
                                   "message": message,
                                   "username" : self.scope["user"].firstName
                                   }
        )

    # Receive message from room group
    async def chat_message(self, event):
        if not self.scope["user"].is_authenticated:
            logger.exception("User not authecatited")
            self.close()
            return
        
        logger.info("User authecatited")
        message = event["message"]
        Message.objects.create(message = message)
        await self.send(text_data=json.dumps({"message": message}))