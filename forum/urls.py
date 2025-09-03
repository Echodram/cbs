# chat/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import room, index, login

urlpatterns = [
    path('forum/choice_room/', index, name='room_choice'),
    path('forum/chat/<str:room_name>/', room, name='room'),
    path('forum/login/', login, name='login')
]