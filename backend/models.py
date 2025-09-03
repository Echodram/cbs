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

