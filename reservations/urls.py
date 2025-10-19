"""
URL patterns для reservations app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ReservationViewSet

app_name = 'reservations'

# Создаем роутер для ViewSet
router = DefaultRouter()
router.register(r'', ReservationViewSet, basename='reservation')

urlpatterns = [
    path('', include(router.urls)),
]
