from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid
from .managers import CustomUserManager
from django.contrib.auth import get_user_model


    
class CustomUser(AbstractBaseUser, PermissionsMixin):
    '''
        description of fields name of custom FIELDS of the table CustomUSer
        
        firstName : First Name of the user
        lastname : Last name of the user
        email : email of the user
        pImage : profil image of the user
        role : role of the user('admin', 'teacher', 'student') 
    '''
    CHOICES = (('teacher', 'TEACHER'),
               ('student', 'STUDENT'),
               ('admin', 'ADMIN'),
               )
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    firstName = models.CharField(max_length=100)
    lastName = models.CharField(max_length=100)
    email = models.EmailField(_("email address"), unique=True)
    pImage = models.ImageField(upload_to='profile_pictures')
    role = models.CharField(max_length=20, choices=CHOICES)
    ###Default fields####
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    paid = models.BooleanField(default=False)
    
    ###Required fields###
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = CustomUserManager()
    bio = models.TextField(max_length=500, blank=True)
    online_status = models.BooleanField(default=False)
    last_seen = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if not self.uuid:
            self.uuid = uuid.uuid3(uuid.NAMESPACE_DNS, self.email)
        super().save(*args, **kwargs)


class PasswordReset(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=100)
    created_at = models.DateTimeField(default=timezone.now)


class Course(models.Model):
    
    LEVEL_CHOICES = (('1', '1'),
                     ('2', '2'),
                     ('3', '3')) ###Courses levels
    
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    teacher = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(max_length=500)
    forum = models.BooleanField(default=False)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    courseCover = models.ImageField(upload_to='courses/courseCover')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title.lower()
        super().save(*args, **kwargs)


class Enrollement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='registrations')
    student = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='registrations')
    registered_on = models.DateTimeField(auto_now_add=True)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)
    
    

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=100)
    file = models.URLField()
    description = models.TextField(max_length=500)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complete = models.BooleanField(default=False)
    open  = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class Book(models.Model):
    title = models.CharField(max_length=100)
    author = models.CharField(max_length=100)
    book = models.FileField(upload_to='books/file')
    category = models.CharField(max_length=50)
    bookCover = models.FileField(upload_to='books/book_cover')
    description = models.TextField(max_length=1000)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    language = models.CharField(max_length=100)
    create_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

class Audio(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    audio = models.FileField(upload_to='teaching', unique=True)
    create_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title.lower()
        super().save(*args, **kwargs)


class Video(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    video = models.FileField(upload_to='teaching', unique=True)
    create_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if self.title:
            self.title = self.title.lower()
        super().save(*args, **kwargs)

class Room(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_private = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='deleted_rooms')
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    
    class Meta:
        permissions = [
            ("can_delete_room", "Can delete room"),
        ]
    
    def __str__(self):
        return self.name
    
    def soft_delete(self, user):
        """Soft delete the room"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user
        self.save()
        
        # Notify all participants via WebSocket
        self.notify_room_deletion()
    
    def hard_delete(self):
        """Permanently delete the room and related data"""
        # Delete all related messages and participants first
        self.messages.all().delete()
        self.participants.all().delete()
        self.delete()
    
    def notify_room_deletion(self):
        """Notify all participants that room was deleted"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{self.id}",
            {
                "type": "room_deleted",
                "room_id": self.id,
                "deleted_by": self.deleted_by.username if self.deleted_by else "System",
            }
        )
    
    def restore(self):
        """Restore a soft-deleted room"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save()

class Message(models.Model):
    room = models.ForeignKey(Room, related_name='messages', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message_type = models.CharField(
        max_length=20, 
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('file', 'File'),
            ('system', 'System')
        ],
        default='text'
    )
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f'{self.user.username}: {self.content[:20]}'
    
    def soft_delete(self):
        """Soft delete the message"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
    
    def edit_message(self, new_content, user):
        """Edit message content with tracking"""
        if not self.original_content and not self.is_edited:
            # First edit - store original content
            self.original_content = self.content
        
        self.content = new_content
        self.is_edited = True
        self.edited_at = timezone.now()
        self.edit_count += 1
        self.save()
        
        # Notify via WebSocket about the edit
        self.notify_message_edit(user)
    
    def notify_message_edit(self, edited_by):
        """Notify WebSocket group about message edit"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"chat_{self.room.id}",
            {
                "type": "message_edited",
                "message_id": self.id,
                "content": self.content,
                "edited_at": self.edited_at.isoformat(),
                "edit_count": self.edit_count,
                "edited_by": edited_by.username,
            }
        )

class RoomParticipant(models.Model):
    room = models.ForeignKey(Room, related_name='participants', on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    class Meta:
        unique_together = ['room', 'user']
    
    def __str__(self):
        return f"{self.user.username} in {self.room.name}"