"""
Views для управления бронированиями с использованием ViewSet.
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Reservation, ReservationStatus
from .serializers import (
    ReservationSerializer,
    ReservationCreateSerializer,
    ReservationUpdateSerializer,
    ReservationListSerializer,
    ReservationStatusUpdateSerializer,
)
from core.permissions import IsReservationParticipant


class ReservationViewSet(viewsets.GenericViewSet):
    """
    ViewSet для управления бронированиями.
    
    list: Список бронирований (с учетом прав доступа)
    retrieve: Детали бронирования
    create: Создание бронирования
    update: Обновление бронирования
    partial_update: Частичное обновление
    destroy: Отмена бронирования
    """
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [permissions.IsAuthenticated, IsReservationParticipant]
    
    def get_serializer_class(self):
        """Выбираем сериализатор"""
        if self.action == 'create':
            return ReservationCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReservationUpdateSerializer
        elif self.action == 'update_status':
            return ReservationStatusUpdateSerializer
        elif self.action == 'list':
            return ReservationListSerializer
        return ReservationSerializer
    
    def get_queryset(self):
        """Фильтрация queryset с учетом прав"""
        user = self.request.user
        queryset = super().get_queryset().select_related(
            'user', 'restaurant', 'table'
        ).order_by('-reservation_date', '-start_time')
        
        # Владельцы видят бронирования своих ресторанов
        if user.is_owner and not user.is_admin_user:
            queryset = queryset.filter(restaurant__owner=user)
        # Обычные пользователи видят только свои бронирования
        elif not user.is_admin_user:
            queryset = queryset.filter(user=user)
        
        # Дополнительные фильтры из query params
        if self.action == 'list':
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
    
    def list(self, request, *args, **kwargs):
        """GET /api/reservations/ - список бронирований"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """GET /api/reservations/<id>/ - детали бронирования"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """POST /api/reservations/ - создание бронирования"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """PUT /api/reservations/<id>/ - полное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/reservations/<id>/ - частичное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """DELETE /api/reservations/<id>/ - отмена бронирования"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        
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
    
    @action(detail=False, methods=['get'])
    def my_reservations(self, request):
        """
        GET /api/reservations/my-reservations/ - бронирования текущего пользователя
        """
        queryset = Reservation.objects.filter(
            user=request.user
        ).select_related('user', 'restaurant', 'table').order_by(
            '-reservation_date', '-start_time'
        )
        
        serializer = ReservationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        GET /api/reservations/upcoming/ - предстоящие бронирования
        """
        user = request.user
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
        
        serializer = ReservationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def past(self, request):
        """
        GET /api/reservations/past/ - прошедшие бронирования
        """
        user = request.user
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
        
        serializer = ReservationListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """
        PATCH /api/reservations/<id>/update-status/ - обновление статуса
        Body: {"status": "confirmed", "note": "optional note"}
        """
        instance = self.get_object()
        user = request.user
        
        # Проверяем права: только владелец ресторана или админ
        if not (instance.restaurant.owner == user or user.is_admin_user):
            return Response({
                'error': 'Only restaurant owner or admin can update reservation status.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'detail': 'Reservation status updated successfully.',
            'reservation': ReservationSerializer(instance).data
        }, status=status.HTTP_200_OK)
