"""
URL patterns для reviews app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReviewViewSet

app_name = 'reviews'

# Создаем роутер для ViewSet
router = DefaultRouter()
router.register(r'', ReviewViewSet, basename='review')

urlpatterns = [
    path('', include(router.urls)),
]
