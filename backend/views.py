from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import get_user_model
from rest_framework import (generics,
                            permissions,
                            viewsets,
                            status)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from .serializers import *
from .models import*
import os

#####User management view
class UserView(viewsets.ModelViewSet):
    '''User registration API view'''
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]
    queryset = get_user_model().objects.all()
    
    def patch(self, request, uuid):
        try:
            user = get_user_model().objects.get(uuid=uuid)
        except Course.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class UserLoginView(generics.CreateAPIView):
    '''User login API view'''
    serializer_class = LoginSerializer
    permission_classes = ()
    authentication_classes = ()

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        user = authenticate(email=email, password=password)
        if user:
            return Response({"token": user.auth_token.key})
        else:
            return Response({"error": "Wrong Credentials"}, status=status.HTTP_400_BAD_REQUEST)
        

class GetTeacherView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        teachers = get_user_model().objects.filter(role='teacher')
        teacher_list = []
        for teacher in teachers:
            info = {}
            courses = Course.objects.filter(teacher=teacher.uuid)
            course_list = []
            if courses:
                for course in courses:
                    datas = {
                        'uuid' : course.uuid,
                        'title' : course.title,
                        'description' : course.description
                    }
                course_list.append(datas)
            
            info = {
                'uuid' : teacher.uuid,
                'firstName' : teacher.firstName,
                'lastName' : teacher.lastName,
                'email' : teacher.email,
                'pImage' : request.build_absolute_uri(teacher.pImage.url),
                'course' : course_list
            }
            teacher_list.append(info)
        return Response(teacher_list)
        
class GetStudentView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        students = get_user_model().objects.filter(role="student")
        student_list = []
        if students is not None:
            for student in students:
                enrollement_list = []
                enrolled_courses = Enrollement.objects.filter(student=student.uuid)
                
                if enrolled_courses:
                    for enroll_course in enrolled_courses:
                        info ={
                            'uuid' : enroll_course.course.uuid,
                            'title' : enroll_course.course.title,
                            'description': enroll_course.course.description
                        }
                        enrollement_list.append(info)
                data = {
                    'uuid': student.uuid,
                    'firstName': student.firstName,
                    'lastName': student.lastName,
                    'email': student.email,
                    'pImage' : request.build_absolute_uri(student.pImage.url),
                    'role' : student.role,
                    'enrolled_course' : enrollement_list
                }
                student_list.append(data)
            return Response(student_list)
    
class GetMe(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request):
        try:
            user = get_user_model().objects.get(uuid=self.request.user.uuid)
            return Response({
                'uuid': user.uuid,
                'email': user.email,
                'firstName': user.firstName,
                'lastName': user.lastName,
                'pImage': request.build_absolute_uri(user.pImage.url)})
        except get_user_model().DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        

class RequestPasswordReset(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = ResetPasswordRequestSerializer
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        email = request.data['email']
        user = get_user_model().objects.filter(email__iexact=email).first()

        if user:
            token_generator = PasswordResetTokenGenerator()
            token = token_generator.make_token(user)
            reset = PasswordReset(email=email, token=token)
            reset.save()

            reset_url = f"http://127.0.0.1:8000/reset/{token}"
            
            subject = 'Password Reset'
            message = f"""
                Dear {user.firstName}
                
                We received a request to reset your password for your account. 
                If you did not make this request, please ignore this email.
                to reset your password, please click the link below:

                {reset_url}
                
                Thank you
            """
            try :
                send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
            except:
                pass

            return Response({'success': 'We have sent you a link to reset your password',
                             'reset_url' : f'{reset_url}'}, 
                            status=status.HTTP_200_OK)
        else:
            return Response({"error": "User with credentials not found"}, status=status.HTTP_404_NOT_FOUND)
        

###Account Management
class ResetPassword(generics.GenericAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = []
    def post(self, request, token):
        User = get_user_model()
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        new_password = data['new_password']
        confirm_password = data['confirm_password']

        if new_password != confirm_password:
            return Response({"error": "Passwords do not match"}, status=400)

        reset_obj = PasswordReset.objects.filter(token=token).first()

        if not reset_obj:
            return Response({'error': 'Invalid token'}, status=400)

        user = User.objects.filter(email=reset_obj.email).first()

        if user:
            user.set_password(request.data['new_password'])
            user.save()

            reset_obj.delete()

            return Response({'success': 'Password updated'})
        else:
            return Response({'error': 'No user found'}, status=404)
        
        
###Courses's views
class CourseView(viewsets.ModelViewSet):
    queryset= Course.objects.prefetch_related('lessons', 'teacher').all()
    serializer_class = CourseSerializer
    permission_classes = []
    def list(self, request):
        scheme = request.scheme
        host = request.get_host()
        full_host_url = f"{scheme}://{host}"
        try:
            datas = []
            for course in self.queryset:
                data = {
                    'id': course.uuid,
                    'title': course.title,
                    'description': course.description,
                    'level': course.level,
                    'courseCover' : request.build_absolute_uri(course.courseCover.url) ,
                    'groupe_chat': course.groupe_chat.id if course.groupe_chat else None,
                    'teacher': {
                        'id': course.teacher.uuid,
                        'firstName': course.teacher.firstName,
                        'lastName': course.teacher.lastName,
                    },
                    'lessons': []
                }

                # Loop through the pre-fetched lessons
                for lesson in course.lessons.all():
                    lesson_data = {
                        'id': lesson.uuid,
                        'title': lesson.title,
                        'description': lesson.description,
                        'file': request.build_absolute_uri(lesson.file.url) if lesson.file else None
                    }
                    data['lessons'].append(lesson_data)
                
                datas.append(data)
            return Response(datas)
        except Exception as e:
            return Response({'error': request.build_absolute_uri(e)}, status=500)
        
        
    def partial_update(self, request, pk=None):
        try:
            course = Course.objects.get(uuid=pk)
        except Course.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CourseSerializer(course, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LessonView(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LessonSerializer
    queryset = Course.objects.prefetch_related('lessons')
    
    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        param1 = request.GET.get('course_uuid', None)
        if param1 is not None:
            data = []
            try:
                course = Course.objects.get(uuid=param1)
                for lesson in course.lessons.all():
                    lesson_data = {
                        'id': lesson.uuid,
                        'title': lesson.title,
                        'description': lesson.description,
                        'file': lesson.file.url if lesson.file else None
                    }
                    data.append(lesson_data)
                return Response({'course_uuid': f"{course.uuid}", "lessons": data})
            except Course.DoesNotExist:
                return Response({'error': 'Course not found'}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({'error': 'course_uuid parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    def partial_update(self, request, pk=None):
        try:
            lesson = Lesson.objects.get(uuid=pk)
        except Lesson.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = LessonSerializer(lesson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        try:
            lesson = Lesson.objects.get(uuid=pk)
            lesson.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Lesson.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        

class EnrollView(generics.CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = EnrollSerializer
    

###Book views
class BookView(viewsets.ModelViewSet):
    permission_classes = []
    serializer_class = BookSerializer
    queryset = Book.objects.all()
    
    def partial_update(self, request, pk=None):
        try:
            lesson = Book.objects.get(uuid=pk)
        except Book.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = BookSerializer(lesson, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    




        

