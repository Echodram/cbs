from django.shortcuts import render
from rest_framework import viewsets
from .models import Blog, Event
from .serializers import BlogSerializer, EventSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status


class BlogViewSet(viewsets.ModelViewSet):
    queryset = Blog.objects.all()
    serializer_class = BlogSerializer   
    permission_classes = [] 
    
    def list(self, request):
        data = []
        for query in self.queryset:
            blog = {
                "id":query.id,
                "title": query.title,
                "content": query.content,
                "author" : query.author,
                "image": request.build_absolute_uri(query.image.url),
                "created_at": query.created_at,
                "updated_at": query.updated_at,
                "description": query.description
            }
            data.append(blog)
        return Response(data, status=status.HTTP_200_OK)

class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer   
    permission_classes = []
    
    def list(self, request):
        data = []
        for query in self.queryset:
            blog = {
                "id" : query.id,
                "title": query.title,
                "content": query.content,
                "image": request.build_absolute_uri(query.image.url),
                "created_at": query.created_at,
                "updated_at": query.updated_at,
                "description": query.description
            }
            data.append(blog)
        return Response(data, status=status.HTTP_200_OK)
            