from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import BlogViewSet, EventViewSet      
from django.conf.urls.static import static
from django.conf import settings
router = DefaultRouter()
router.register(r'blogs', BlogViewSet, basename='blog')
router.register(r'event',EventViewSet, basename='event')

urlpatterns = [
    path('', include(router.urls)),
] +  static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

