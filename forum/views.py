from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from backend.models import Room, Message, RoomParticipant, CustomUser
from .serializers import RoomSerializer, MessageSerializer, MessageEditSerializer, CustomUserSerializer
from datetime import timezone
from collections import defaultdict

class IsRoomParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'room'):
            return RoomParticipant.objects.filter(room=obj.room, user=request.user).exists()
        return RoomParticipant.objects.filter(room=obj, user=request.user).exists()

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            return Room.objects.filter(
                Q(is_private=False) | 
                Q(participants__user=user)
            ).distinct()
        return Room.objects.filter(is_private=False)
    
    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user)
        RoomParticipant.objects.create(room=room, user=self.request.user, is_admin=True)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, pk=None):
        room = self.get_object()
        participant, created = RoomParticipant.objects.get_or_create(
            room=room, 
            user=request.user
        )
        
        if created:
            return Response({'status': 'joined room'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'already in room'}, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        room = self.get_object()
        messages = room.messages.all().order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        room = self.get_object()
        participants = room.participants.all().order_by('-is_admin', 'joined_at')
        from .serializers import RoomParticipantSerializer
        serializer = RoomParticipantSerializer(participants, many=True)
        return Response(serializer.data)

class IsRoomAdmin(permissions.BasePermission):
    """Check if user can delete the room"""
    def has_object_permission(self, request, view, obj):
        if request.method in ['DELETE'] or view.action == 'delete_room':
            # Room creator can always delete
            if obj.created_by == request.user:
                return True
            # Check if user is admin participant with delete rights
            participant = obj.participants.filter(user=request.user).first()
            return participant and (participant.is_admin or participant.can_delete)
        return True

class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated, IsRoomAdmin]
    
    def get_queryset(self):
        user = self.request.user
        # Exclude deleted rooms by default
        show_deleted = self.request.query_params.get('show_deleted', 'false').lower() == 'true'
        
        queryset = Room.objects.filter(
            Q(is_private=False) | 
            Q(participants__user=user)
        ).distinct()
        
        if not show_deleted:
            queryset = queryset.filter(is_deleted=False)
            
        return queryset
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, pk=None):
        room = self.get_object()
        participant, created = RoomParticipant.objects.get_or_create(
            room=room, 
            user=request.user
        )
    
        if created:
            return Response({'status': 'joined room'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'already in room'}, status=status.HTTP_200_OK)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    def perform_create(self, serializer):
        room = serializer.save(created_by=self.request.user)
        # Add creator as admin participant with delete rights
        RoomParticipant.objects.create(
            room=room, 
            user=self.request.user, 
            is_admin=True,
            can_delete=True
        )
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        room = self.get_object()
        messages = room.messages.all().order_by('timestamp')
        serializer = MessageSerializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        room = self.get_object()
        participants = room.participants.all().order_by('-is_admin', 'joined_at')
        from .serializers import RoomParticipantSerializer
        serializer = RoomParticipantSerializer(participants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsRoomAdmin])
    def delete_room(self, request, pk=None):
        """Soft or hard delete a room"""
        room = self.get_object()
        serializer = RoomDeleteSerializer(data=request.data)
        
        if serializer.is_valid():
            permanent = serializer.validated_data['permanent']
            
            if permanent:
                # Hard delete - only room creator can do this
                if room.created_by != request.user:
                    return Response(
                        {'error': 'Only room creator can permanently delete rooms'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                room_name = room.name
                room.hard_delete()
                return Response(
                    {'status': f'Room "{room_name}" permanently deleted'},
                    status=status.HTTP_200_OK
                )
            else:
                # Soft delete
                room.soft_delete(request.user)
                return Response(
                    {'status': f'Room "{room.name}" has been deleted'},
                    status=status.HTTP_200_OK
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def rooms_with_messages(self, request):
        """
        Get all rooms with their messages for the current user
        Query parameters:
          - include_messages: true/false (default: true)
          - messages_limit: number of messages per room (default: 50)
          - offset: pagination offset (default: 0)
        """
        user = request.user
        
        # Get parameters with defaults
        include_messages = request.query_params.get('include_messages', 'true').lower() == 'true'
        messages_limit = int(request.query_params.get('messages_limit', 50))
        offset = int(request.query_params.get('offset', 0))
        
        # Get rooms accessible to user
        rooms = self.get_queryset()
        
        if include_messages:
            # Get room IDs
            room_ids = rooms.values_list('uuid', flat=True)
            
            # Get messages for these rooms with pagination
            messages = Message.objects.filter(
                room_id__in=room_ids,
                is_deleted=False
            ).order_by('-timestamp')[offset:offset + messages_limit]
            
            # Organize messages by room
            messages_by_room = defaultdict(list)
            for message in messages:
                messages_by_room[message.room_id].append(message)
            
            # Serialize rooms with their messages
            rooms_data = []
            for room in rooms:
                room_data = RoomSerializer(room, context={'request': request}).data
                
                if room.uuid in messages_by_room:
                    # Get messages for this room and order them chronologically
                    room_messages = sorted(
                        messages_by_room[room.uuid], 
                        key=lambda x: x.timestamp
                    )
                    room_data['messages'] = MessageSerializer(
                        room_messages, 
                        many=True,
                        context={'request': request}
                    ).data
                else:
                    room_data['messages'] = []
                
                rooms_data.append(room_data)
            
            return Response({
                'count': len(rooms_data),
                'rooms': rooms_data,
                'has_more': len(messages) == messages_limit
            })
        
        else:
            # Just return rooms without messages
            serializer = RoomSerializer(rooms, many=True, context={'request': request})
            return Response({
                'count': rooms.count(),
                'rooms': serializer.data
            })
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def recent_messages(self, request):
        """
        Get all recent messages across all rooms for the user
        Useful for showing a unified chat feed
        """
        user = request.user
        
        # Get accessible rooms
        accessible_rooms = self.get_queryset()
        room_ids = accessible_rooms.values_list('id', flat=True)
        
        # Get recent messages
        limit = int(request.query_params.get('limit', 100))
        offset = int(request.query_params.get('offset', 0))
        
        messages = Message.objects.filter(
            room_id__in=room_ids,
            is_deleted=False
        ).select_related('user', 'room').order_by('-timestamp')[offset:offset + limit]
        
        # Organize by date
        messages_by_date = defaultdict(list)
        for message in messages:
            date_str = message.timestamp.date().isoformat()
            messages_by_date[date_str].append(message)
        
        # Serialize
        result = []
        for date_str, msgs in sorted(messages_by_date.items(), reverse=True):
            result.append({
                'date': date_str,
                'messages': MessageSerializer(
                    sorted(msgs, key=lambda x: x.timestamp, reverse=True),
                    many=True,
                    context={'request': request}
                ).data
            })
        
        return Response({
            'count': messages.count(),
            'messages_by_date': result,
            'has_more': len(messages) == limit
        })
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsRoomAdmin])
    def restore_room(self, request, pk=None):
        """Restore a soft-deleted room"""
        room = self.get_object()
        
        if not room.is_deleted:
            return Response(
                {'error': 'Room is not deleted'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        room.restore()
        return Response(
            {'status': f'Room "{room.name}" has been restored'},
            status=status.HTTP_200_OK
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def leave_room(self, request, pk=None):
        """Leave a room (for participants)"""
        room = self.get_object()
        
        if room.created_by == request.user:
            return Response(
                {'error': 'Room creator cannot leave the room. Transfer ownership or delete the room.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        participant = room.participants.filter(user=request.user).first()
        if participant:
            participant.delete()
            return Response(
                {'status': f'You have left room "{room.name}"'},
                status=status.HTTP_200_OK
            )
        
        return Response(
            {'error': 'You are not a participant of this room'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsRoomAdmin])
    def remove_participant(self, request, pk=None):
        """Remove a participant from the room (admin only)"""
        room = self.get_object()
        participant_id = request.data.get('participant_id')
        
        if not participant_id:
            return Response(
                {'error': 'participant_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            participant = room.participants.get(id=participant_id)
            
            # Cannot remove room creator
            if participant.user == room.created_by:
                return Response(
                    {'error': 'Cannot remove room creator'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            participant_name = participant.user.username
            participant.delete()
            
            return Response(
                {'status': f'Removed {participant_name} from room'},
                status=status.HTTP_200_OK
            )
            
        except RoomParticipant.DoesNotExist:
            return Response(
                {'error': 'Participant not found in this room'},
                status=status.HTTP_404_NOT_FOUND
            )

class MessageViewSet(viewsets.ModelViewSet):
    serializer_class = MessageSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        room_id = self.request.query_params.get('room_id')
        if room_id:
            return Message.objects.filter(
                room_id=room_id, 
                is_deleted=False
            ).order_by('timestamp')
        return Message.objects.none()
    
    def get_serializer_class(self):
        """Use different serializer for different actions"""
        if self.action == 'partial_update':
            return MessageEditSerializer
        return super().get_serializer_class()
    
    def perform_create(self, serializer):
        message = serializer.save(user=self.request.user)
        
        # Send message to WebSocket group
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.room.uuid}",
            {
                "type": "chat_message",
                "message": MessageSerializer(message, context=self.get_serializer_context()).data
            }
        )
    
    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests for editing messages"""
        instance = self.get_object()
        
        # Check if user can edit this message
        can_edit = self._can_edit_message(instance, request.user)
        if not can_edit['allowed']:
            return Response(
                {'error': can_edit['reason']},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Use the model's edit method to track changes
        instance.edit_message(serializer.validated_data['content'], request.user)
        
        # Serialize the updated message for response
        updated_serializer = MessageSerializer(instance, context=self.get_serializer_context())
        return Response(updated_serializer.data)
    
    def _can_edit_message(self, message, user):
        """Check if user can edit the message"""
        # Cannot edit deleted messages
        if message.is_deleted:
            return {'allowed': False, 'reason': 'Cannot edit deleted message'}
        
        # User must be the message owner
        if message.user != user:
            return {'allowed': False, 'reason': 'You can only edit your own messages'}
        
        # Check edit time window (15 minutes)
        time_since_creation = timezone.now() - message.timestamp
        if time_since_creation.total_seconds() > 900:  # 15 minutes
            return {'allowed': False, 'reason': 'Message can only be edited within 15 minutes of posting'}
        
        return {'allowed': True, 'reason': ''}
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def edit_history(self, request, pk=None):
        """Get message edit history"""
        message = self.get_object()
        
        # Only message owner and room admins can see edit history
        if message.user != request.user:
            room_admin = RoomParticipant.objects.filter(
                room=message.room,
                user=request.user,
                is_admin=True
            ).exists()
            if not room_admin:
                return Response(
                    {'error': 'You cannot view edit history for this message'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        history_data = {
            'id': message.id,
            'current_content': message.content,
            'original_content': message.original_content if message.is_edited else message.content,
            'is_edited': message.is_edited,
            'edit_count': message.edit_count,
            'edited_at': message.edited_at,
            'created_at': message.timestamp,
        }
        
        return Response(history_data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def delete_message(self, request, pk=None):
        """Soft delete a message"""
        message = self.get_object()
        
        # Users can only delete their own messages unless they're room admins
        if message.user != request.user:
            room_admin = RoomParticipant.objects.filter(
                room=message.room,
                user=request.user,
                is_admin=True
            ).exists()
            
            if not room_admin:
                return Response(
                    {'error': 'You can only delete your own messages'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        message.soft_delete()
        
        # Notify WebSocket about deletion
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{message.room.id}",
            {
                "type": "message_deleted",
                "message_id": message.id,
                "deleted_by": request.user.username,
            }
        )
        
        return Response(
            {'status': 'Message deleted'},
            status=status.HTTP_200_OK
        )
    
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return CustomUser.objects.all()
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def online(self, request):
        online_users = CustomUser.objects.filter(online_status=True)
        serializer = self.get_serializer(online_users, many=True)
        return Response(serializer.data)