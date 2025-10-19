"""
Views для управления бронированиями.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q
from django.utils import timezone

from .models import Reservation, ReservationStatus
from .serializers import (
    ReservationSerializer,
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
    ReservationListSerializer,
    ReservationStatusUpdateSerializer,
    ReservationMinimalSerializer
)


class ReservationListCreateView(generics.ListCreateAPIView):
    """
    Список бронирований и создание нового бронирования.
    GET /api/reservations/
    POST /api/reservations/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReservationCreateSerializer
        return ReservationListSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Reservation.objects.select_related(
            'user', 'restaurant', 'table'
        ).order_by('-reservation_date', '-start_time')
        
        # Фильтрация для владельцев ресторанов
        if user.is_owner and not user.is_admin_user:
            queryset = queryset.filter(restaurant__owner=user)
        # Фильтрация для обычных пользователей
        elif not user.is_admin_user:
            queryset = queryset.filter(user=user)
        
        # Фильтр по статусу
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Фильтр по ресторану
        restaurant_id = self.request.query_params.get('restaurant', None)
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        # Фильтр по дате
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        if date_from:
            queryset = queryset.filter(reservation_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(reservation_date__lte=date_to)
        
        return queryset
    
    def perform_create(self, serializer):
        """Устанавливаем пользователя бронирования"""
        serializer.save(user=self.request.user)


class ReservationDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Детальная информация о бронировании, обновление и отмена.
    GET /api/reservations/<id>/
    PUT/PATCH /api/reservations/<id>/
    DELETE /api/reservations/<id>/ (отмена)
    """
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReservationUpdateSerializer
        return ReservationSerializer
    
    def get_queryset(self):
        user = self.request.user
        queryset = Reservation.objects.select_related('user', 'restaurant', 'table')
        
        # Владельцы видят бронирования своих ресторанов
        if user.is_owner and not user.is_admin_user:
            return queryset.filter(restaurant__owner=user)
        # Обычные пользователи видят только свои бронирования
        elif not user.is_admin_user:
            return queryset.filter(user=user)
        
        return queryset
    
    def check_object_permissions(self, request, obj):
        """Проверяем права доступа"""
        super().check_object_permissions(request, obj)
        
        # Владелец бронирования может все
        if obj.user == request.user:
            return
        
        # Владелец ресторана может просматривать и менять статус
        if obj.restaurant.owner == request.user:
            if request.method in ['PUT', 'PATCH', 'DELETE']:
                # Но не может менять детали бронирования гостя
                if request.method != 'DELETE':
                    return
        
        # Админ может все
        if request.user.is_admin_user:
            return
        
        self.permission_denied(
            request,
            message='You do not have permission to access this reservation.'
        )
    
    def destroy(self, request, *args, **kwargs):
        """Отмена бронирования"""
        instance = self.get_object()
        
        # Проверяем, можно ли отменить
        if instance.status in [ReservationStatus.COMPLETED, ReservationStatus.NO_SHOW]:
            return Response({
                'error': 'Cannot cancel completed or no-show reservations.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if instance.status == ReservationStatus.CANCELLED:
            return Response({
                'error': 'Reservation is already cancelled.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        instance.cancel()
        
        return Response({
            'detail': 'Reservation cancelled successfully.'
        }, status=status.HTTP_200_OK)


class MyReservationsView(generics.ListAPIView):
    """
    Бронирования текущего пользователя.
    GET /api/reservations/my/
    """
    serializer_class = ReservationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Reservation.objects.filter(
            user=self.request.user
        ).select_related('user', 'restaurant', 'table').order_by(
            '-reservation_date', '-start_time'
        )


class RestaurantReservationsView(generics.ListAPIView):
    """
    Бронирования для ресторана (только владелец ресторана).
    GET /api/restaurants/<restaurant_id>/reservations/
    """
    serializer_class = ReservationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        restaurant_id = self.kwargs['restaurant_id']
        user = self.request.user
        
        queryset = Reservation.objects.filter(
            restaurant_id=restaurant_id
        ).select_related('user', 'restaurant', 'table').order_by(
            '-reservation_date', '-start_time'
        )
        
        # Проверяем права доступа
        if not user.is_admin_user:
            # Проверяем, что пользователь - владелец ресторана
            if not queryset.filter(restaurant__owner=user).exists():
                return Reservation.objects.none()
        
        return queryset


class ReservationStatusUpdateView(generics.UpdateAPIView):
    """
    Обновление статуса бронирования (только владелец ресторана или admin).
    PATCH /api/reservations/<id>/status/
    Body: {"status": "confirmed", "note": "optional note"}
    """
    serializer_class = ReservationStatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Reservation.objects.all()
    
    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()
        
        # Владельцы видят только свои рестораны
        if user.is_owner and not user.is_admin_user:
            return queryset.filter(restaurant__owner=user)
        
        # Админы видят все
        if user.is_admin_user:
            return queryset
        
        # Обычные пользователи не могут менять статус
        return Reservation.objects.none()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'detail': 'Reservation status updated successfully.',
            'reservation': ReservationSerializer(instance).data
        }, status=status.HTTP_200_OK)


class UpcomingReservationsView(generics.ListAPIView):
    """
    Предстоящие бронирования (на сегодня и будущее).
    GET /api/reservations/upcoming/
    """
    serializer_class = ReservationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        
        queryset = Reservation.objects.filter(
            reservation_date__gte=today
        ).exclude(
            status__in=[ReservationStatus.CANCELLED, ReservationStatus.NO_SHOW]
        ).select_related('user', 'restaurant', 'table').order_by(
            'reservation_date', 'start_time'
        )
        
        # Фильтрация по роли
        if user.is_owner and not user.is_admin_user:
            queryset = queryset.filter(restaurant__owner=user)
        elif not user.is_admin_user:
            queryset = queryset.filter(user=user)
        
        return queryset


class PastReservationsView(generics.ListAPIView):
    """
    Прошедшие бронирования.
    GET /api/reservations/past/
    """
    serializer_class = ReservationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        today = timezone.now().date()
        
        queryset = Reservation.objects.filter(
            reservation_date__lt=today
        ).select_related('user', 'restaurant', 'table').order_by(
            '-reservation_date', '-start_time'
        )
        
        # Фильтрация по роли
        if user.is_owner and not user.is_admin_user:
            queryset = queryset.filter(restaurant__owner=user)
        elif not user.is_admin_user:
            queryset = queryset.filter(user=user)
        
        return queryset
