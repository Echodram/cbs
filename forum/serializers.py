from rest_framework import serializers
from backend.models import CustomUser, Room, Message, RoomParticipant
from datetime import  timezone

class CustomUserSerializer(serializers.ModelSerializer):
    online_status = serializers.BooleanField(read_only=True)
    last_seen = serializers.DateTimeField(read_only=True)
    
    class Meta:
        model = CustomUser
        fields = ['uuid', 'firstName', 'email', 'lastName', 
                  'bio', 'online_status', 'last_seen'] 
        read_only_fields = ['online_status', 'last_seen']

class RoomParticipantSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    
    class Meta:
        model = RoomParticipant
        fields = ['user', 'joined_at', 'is_admin']

class RoomSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField(read_only=True)
    participants_count = serializers.SerializerMethodField()
    online_count = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Room
        fields = [
            'uuid', 'name', 'description', 'created_at', 'created_by', 
            'is_private', 'is_deleted', 'deleted_at', 'deleted_by',
            'participants_count', 'online_count', 'can_delete'
        ]
        read_only_fields = ['is_deleted', 'deleted_at', 'deleted_by']
    
    def get_participants_count(self, obj):
        return obj.participants.count()
    
    def get_online_count(self, obj):
        return CustomUser.objects.filter(
            uuid__in=obj.participants.values_list('user_id', flat=True),
            online_status=True
        ).count()
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Check if user is room creator or has admin privileges
            if obj.created_by == request.user:
                return True
            # Check if user is admin participant
            participant = obj.participants.filter(user=request.user).first()
            return participant and (participant.is_admin or participant.can_delete)
        return False

class RoomDeleteSerializer(serializers.Serializer):
    confirmation = serializers.BooleanField(
        required=True,
        error_messages={
            'required': 'Please confirm deletion by setting confirmation=true'
        }
    )
    permanent = serializers.BooleanField(default=False)

class MessageSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
   
    
    class Meta:
        model = Message
        fields = [
            'uuid', 'room', 'user', 'content', 'timestamp', 
            'message_type', 'is_deleted', 'deleted_at',
        ]
        read_only_fields = [
            'uuid', 'user', 'timestamp', 'is_deleted', 'deleted_at',
        ]
    
    def get_can_edit(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Users can edit their own messages within time limit
            if obj.user == request.user:
                # Check if within edit time window (e.g., 15 minutes)
                time_since_creation = timezone.now() - obj.timestamp
                return time_since_creation.total_seconds() <= 900  # 15 minutes
        return False
    
    def get_can_delete(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            # Users can delete their own messages or admins can delete any
            if obj.user == request.user:
                return True
            # Check if user is room admin
            room_admin = RoomParticipant.objects.filter(
                room=obj.room,
                user=request.user,
                is_admin=True
            ).exists()
            return room_admin
        return False

class MessageEditSerializer(serializers.ModelSerializer):
    """Serializer specifically for editing messages"""
    class Meta:
        model = Message
        fields = ['content']
    
    def validate_content(self, value):
        """Validate message content"""
        value = value.strip()
        if len(value) == 0:
            raise serializers.ValidationError("Message content cannot be empty")
        if len(value) > 10000:
            raise serializers.ValidationError("Message is too long")
        return value