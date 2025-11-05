import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from backend.models import Room, Message, RoomParticipant

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        self.user = self.scope["user"]
        
        # Check if user is authenticated and can join the room
        if not await self.can_join_room():
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Update user online status
        await self.update_user_online_status(True)
        
        # Add user to room participants if not already
        await self.add_user_to_participants()
        
        # Send join message to group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_activity',
                'activity_type': 'user_join',
                'user': await self.get_user_data(),
                'online_count': await self.get_online_count()
            }
        )
        
        # Send current online users to the joining user
        await self.send_online_users()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            # Update user online status
            await self.update_user_online_status(False)
            
            # Send leave message to group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_activity',
                    'activity_type': 'user_leave',
                    'user': await self.get_user_data(),
                    'online_count': await self.get_online_count()
                }
            )
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type', 'chat_message')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'typing':
                await self.handle_typing_indicator(text_data_json)
            elif message_type == 'read_receipt':
                await self.handle_read_receipt(text_data_json)
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'error': 'Invalid JSON format'
            }))

    async def handle_chat_message(self, data):
        message_content = data.get('message', '').strip()
        
        if not message_content or not self.user.is_authenticated:
            return
        
        # Save message to database
        saved_message = await self.save_message(message_content)
        
        if saved_message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': await self.serialize_message(saved_message)
                }
            )
    async def message_edited(self, event):
        """Handle message edit notification"""
        await self.send(text_data=json.dumps({
            'type': 'message_edited',
            'message_id': event['message_id'],
            'content': event['content'],
            'edited_at': event['edited_at'],
            'edit_count': event['edit_count'],
            'edited_by': event['edited_by'],
        }))
    
    async def message_deleted(self, event):
        """Handle message deletion notification"""
        await self.send(text_data=json.dumps({
            'type': 'message_deleted',
            'message_id': event['message_id'],
            'deleted_by': event['deleted_by'],
        }))

    async def handle_typing_indicator(self, data):
        is_typing = data.get('typing', False)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': await self.get_user_data(),
                'typing': is_typing
            }
        )
        
    async def handle_read_receipt(self, data):
        message_id = data.get('message_id')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'read_receipt',
                'user': await self.get_user_data(),
                'message_id': message_id
            }
        )

    # Handler methods for different message types
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message']
        }))

    async def user_activity(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_activity',
            'activity_type': event['activity_type'],
            'user': event['user'],
            'online_count': event['online_count'],
            'timestamp': await self.get_current_timestamp()
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing_indicator',
            'user': event['user'],
            'typing': event['typing']
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'user': event['user'],
            'message_id': event['message_id']
        }))

    # Database operations
    @database_sync_to_async
    def can_join_room(self):
        if not self.user.is_authenticated:
            return False
        try:
            room = Room.objects.get(id=self.room_id)
            if room.is_private:
                return RoomParticipant.objects.filter(room=room, user=self.user).exists()
            return True
        except Room.DoesNotExist:
            return False

    @database_sync_to_async
    def update_user_online_status(self, status):
        if self.user.is_authenticated:
            User.objects.filter(id=self.user.id).update(online_status=status)

    @database_sync_to_async
    def add_user_to_participants(self):
        if self.user.is_authenticated:
            room = Room.objects.get(id=self.room_id)
            RoomParticipant.objects.get_or_create(room=room, user=self.user)

    @database_sync_to_async
    def save_message(self, content):
        try:
            room = Room.objects.get(id=self.room_id)
            return Message.objects.create(
                room=room,
                user=self.user,
                content=content
            )
        except Room.DoesNotExist:
            return None

    @database_sync_to_async
    def serialize_message(self, message):
        from .serializers import MessageSerializer
        return MessageSerializer(message).data

    @database_sync_to_async
    def get_user_data(self):
        from .serializers import CustomUserSerializer
        return CustomUserSerializer(self.user).data

    @database_sync_to_async
    def get_online_count(self):
        room = Room.objects.get(id=self.room_id)
        participant_ids = room.participants.values_list('user_id', flat=True)
        return User.objects.filter(
            id__in=participant_ids,
            online_status=True
        ).count()

    @database_sync_to_async
    def get_online_users(self):
        room = Room.objects.get(uuid=self.room_id)
        participant_ids = room.participants.values_list('user_id', flat=True)
        online_users = User.objects.filter(
            id__in=participant_ids,
            online_status=True
        )
        from .serializers import CustomUserSerializer
        return CustomUserSerializer(online_users, many=True).data

    @database_sync_to_async
    def get_current_timestamp(self):
        from django.utils import timezone
        return timezone.now().isoformat()

    async def send_online_users(self):
        online_users = await self.get_online_users()
        await self.send(text_data=json.dumps({
            'type': 'online_users',
            'users': online_users
        }))