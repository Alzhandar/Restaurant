"""
URL patterns для restaurants app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import RestaurantViewSet, TableViewSet

app_name = 'restaurants'

# Создаем роутер для ViewSets
router = DefaultRouter()
router.register(r'restaurants', RestaurantViewSet, basename='restaurant')
router.register(r'tables', TableViewSet, basename='table')

urlpatterns = [
    path('', include(router.urls)),
]
