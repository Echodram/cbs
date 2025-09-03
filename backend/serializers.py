from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import *
from supabase import create_client
from django.conf import settings



class ModelSupabaseSerializer(serializers.ModelSerializer):
    
    file = serializers.FileField(write_only=True)
    
    class Meta:
        pass
    
    def upload_to_supabase(self, file_obj):
        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        bucket_name = getattr(self.Meta, 'bucket_name', 'default-bucket')
        file_path = f"uploads/{file_obj.name}"
        response = supabase.storage.from_(bucket_name).upload(file_path, file_obj.read())
        if response.get("error"):
            raise serializers.ValidationError(f"Supabase upload error: {response['error']['message']}")
        public_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket_name}/{file_path}"
        return public_url

    def create(self, validated_data):
        file_obj = validated_data.pop('file')
        public_url = self.upload_to_supabase(file_obj)

        return self.Meta.model.objects.create(
            file_name=file_obj.name,
            file_url=public_url,
            **validated_data
        )
    

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    pImage = serializers.FileField()
    class Meta:
        User = get_user_model()
        model = User
        fields = "__all__"
        
    def create(self, validated_data):
        User = get_user_model()
        user = User.objects.create_user(email = validated_data['email'], 
                                        password = validated_data['password'], 
                                        role = validated_data['role'],
                                        firstName = validated_data["firstName"],
                                        lastName =  validated_data["lastName"],
                                        pImage = validated_data['pImage']
                                        )
        Token.objects.create(user=user)
        return user
    
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only = True)
    password = serializers.CharField(write_only = True)

class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)

class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.RegexField(regex=r'^(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$',
                                          write_only=True,
                                          error_messages={'invalid': ('Password must be at least 8 characters long with at least one capital letter and symbol')})
    confirm_password = serializers.CharField(write_only=True, required=True)


class CourseSerializer(ModelSupabaseSerializer):
    """
    CourseSerializer is a Django REST Framework serializer for the Course model.
    Overview:
        This serializer handles the serialization and deserialization of Course instances,
        including validation and creation logic. It ensures that only users with the role
        of 'teacher' can be assigned as the teacher for a course. The serializer exposes
        all fields of the Course model and provides a custom create method for instantiating
    Course objects from validated data.
    Fields:
    - teacher: PrimaryKeyRelatedField limited to users with the 'teacher' role.
    Methods:
    - create(validated_data): Creates and returns a new Course instance using the provided validated data.
    """
    User = get_user_model()
    teacher = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='teacher'))
    class Meta:
        model = Course
        fields =  "__all__"
        
    def create(self, validated_data):
        course = Course(title = validated_data['title'],
                        description=validated_data['description'],
                        teacher = validated_data['teacher'],
                        level = validated_data['level'],
                        courseCover = validated_data['courseCover'])
        course.save()
        return course

class LessonSerializer(serializers.ModelSerializer):
    """
    LessonSerializer is a ModelSerializer for the Lesson model.
    Overview:
        This serializer handles the serialization and deserialization of Lesson instances,
        including validation and creation logic. It exposes all fields of the Lesson model,
        and represents the related Course as a primary key.
    Fields:
        - course: PrimaryKeyRelatedField to associate a Lesson with a Course.
        - All other fields from the Lesson model are included.
    Methods:
        - create(validated_data): Custom creation logic for Lesson instances using validated data.
    """
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    class Meta:
        model = Lesson
        fields = "__all__"
            
    def create(self, validated_data):
        lesson = Lesson(title = validated_data['title'],
                        description=validated_data['description'],
                        file=validated_data['file'],
                        course = validated_data['course']
                        )
        lesson.save()
        return lesson
    

class EnrollSerializer(serializers.ModelSerializer):
    """
    EnrollSerializer is a ModelSerializer for handling enrollment of students in courses.
    Overview:
        This serializer manages the serialization and deserialization of Enrollement model instances,
        specifically for associating a student with a course. It ensures that only users with the
        'student' role can be enrolled and that the referenced course exists.
    Fields:
        - course: Primary key reference to a Course instance.
        - student: Primary key reference to a User instance with the 'student' role.
    Usage:
        Use this serializer to validate and create enrollment records linking students to courses.
    """
    
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    student = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.filter(role = 'student'))
    class Meta:
        model = Enrollement
        fields = ('course', 'student')
    
        def create(self, validated_data):
            enrolloment = Enrollement(student=validated_data['student'],
                                      course=validated_data['course'],
                                      )
            enrolloment.save()
            


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"
        
        
class ResetPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
