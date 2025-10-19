"""
Views для управления отзывами.
"""
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Avg, Count, Q

from .models import Review
from .serializers import (
    ReviewSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer,
    ReviewListSerializer,
    RestaurantReviewSerializer,
    ReviewStatsSerializer
)
from reservations.models import Reservation, ReservationStatus


class ReviewListCreateView(generics.ListCreateAPIView):
    """
    Список отзывов и создание нового отзыва.
    GET /api/reviews/
    POST /api/reviews/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewListSerializer
    
    def get_queryset(self):
        queryset = Review.objects.select_related(
            'user', 'restaurant', 'reservation'
        ).order_by('-created_at')
        
        # Фильтр по ресторану
        restaurant_id = self.request.query_params.get('restaurant', None)
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        # Фильтр по пользователю
        user_id = self.request.query_params.get('user', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Фильтр по рейтингу
        min_rating = self.request.query_params.get('min_rating', None)
        if min_rating:
            queryset = queryset.filter(rating__gte=int(min_rating))
        
        return queryset
    
    def perform_create(self, serializer):
        """Устанавливаем пользователя отзыва"""
        serializer.save(user=self.request.user)


class ReviewDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Детальная информация об отзыве, обновление и удаление.
    GET /api/reviews/<id>/
    PUT/PATCH /api/reviews/<id>/ (только автор или admin)
    DELETE /api/reviews/<id>/ (только автор или admin)
    """
    queryset = Review.objects.all()
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ReviewUpdateSerializer
        return ReviewSerializer
    
    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]
    
    def check_object_permissions(self, request, obj):
        """Проверяем, что пользователь - автор отзыва или админ"""
        super().check_object_permissions(request, obj)
        
        if request.method in ['PUT', 'PATCH', 'DELETE']:
            if not (obj.user == request.user or request.user.is_admin_user):
                self.permission_denied(
                    request,
                    message='You do not have permission to modify this review.'
                )


class MyReviewsView(generics.ListAPIView):
    """
    Отзывы текущего пользователя.
    GET /api/reviews/my/
    """
    serializer_class = ReviewListSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Review.objects.filter(
            user=self.request.user
        ).select_related('user', 'restaurant', 'reservation').order_by('-created_at')


class RestaurantReviewsView(generics.ListAPIView):
    """
    Все отзывы для конкретного ресторана.
    GET /api/restaurants/<restaurant_id>/reviews/
    """
    serializer_class = RestaurantReviewSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        restaurant_id = self.kwargs['restaurant_id']
        return Review.objects.filter(
            restaurant_id=restaurant_id
        ).select_related('user').order_by('-created_at')


class RestaurantReviewStatsView(APIView):
    """
    Статистика отзывов для ресторана.
    GET /api/restaurants/<restaurant_id>/reviews/stats/
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, restaurant_id):
        reviews = Review.objects.filter(restaurant_id=restaurant_id)
        
        if not reviews.exists():
            return Response({
                'restaurant_id': restaurant_id,
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {
                    '5': 0, '4': 0, '3': 0, '2': 0, '1': 0
                }
            }, status=status.HTTP_200_OK)
        
        # Вычисляем статистику
        stats = reviews.aggregate(
            total=Count('id'),
            average=Avg('rating')
        )
        
        # Распределение по рейтингам
        distribution = {
            '5': reviews.filter(rating=5).count(),
            '4': reviews.filter(rating=4).count(),
            '3': reviews.filter(rating=3).count(),
            '2': reviews.filter(rating=2).count(),
            '1': reviews.filter(rating=1).count(),
        }
        
        return Response({
            'restaurant_id': restaurant_id,
            'total_reviews': stats['total'],
            'average_rating': round(stats['average'], 2) if stats['average'] else 0,
            'rating_distribution': distribution
        }, status=status.HTTP_200_OK)


class UserCanReviewView(APIView):
    """
    Проверка, может ли пользователь оставить отзыв на ресторан.
    GET /api/restaurants/<restaurant_id>/can-review/
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, restaurant_id):
        user = request.user
        
        # Проверяем, есть ли завершенное бронирование
        completed_reservations = Reservation.objects.filter(
            user=user,
            restaurant_id=restaurant_id,
            status=ReservationStatus.COMPLETED
        )
        
        if not completed_reservations.exists():
            return Response({
                'can_review': False,
                'reason': 'You need to have a completed reservation to leave a review.'
            }, status=status.HTTP_200_OK)
        
        # Проверяем, не оставлен ли уже отзыв
        existing_review = Review.objects.filter(
            user=user,
            restaurant_id=restaurant_id
        ).first()
        
        if existing_review:
            return Response({
                'can_review': False,
                'reason': 'You have already reviewed this restaurant.',
                'review_id': existing_review.id
            }, status=status.HTTP_200_OK)
        
        return Response({
            'can_review': True,
            'completed_reservations': completed_reservations.count()
        }, status=status.HTTP_200_OK)


class LatestReviewsView(generics.ListAPIView):
    """
    Последние отзывы по всем ресторанам.
    GET /api/reviews/latest/
    """
    serializer_class = ReviewListSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Review.objects.select_related(
        'user', 'restaurant'
    ).order_by('-created_at')[:20]  # Последние 20 отзывов
