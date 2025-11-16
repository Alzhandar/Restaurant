from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count
from django.core.cache import cache
from django.utils.http import urlencode

from .models import Review
from .serializers import (
    ReviewSerializer,
    ReviewCreateSerializer,
    ReviewUpdateSerializer,
    ReviewListSerializer,
    RestaurantReviewSerializer,
)
from reservations.models import Reservation, ReservationStatus
from core.permissions import IsReviewAuthorOrReadOnly


class ReviewViewSet(viewsets.GenericViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'latest']:
            return [permissions.AllowAny()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsReviewAuthorOrReadOnly()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ReviewUpdateSerializer
        elif self.action == 'list':
            return ReviewListSerializer
        return ReviewSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related(
            'user', 'restaurant', 'reservation'
        ).order_by('-created_at')
        
        if self.action == 'list':
            restaurant_id = self.request.query_params.get('restaurant', None)
            if restaurant_id:
                queryset = queryset.filter(restaurant_id=restaurant_id)
            
            user_id = self.request.query_params.get('user', None)
            if user_id:
                queryset = queryset.filter(user_id=user_id)
            
            min_rating = self.request.query_params.get('min_rating', None)
            if min_rating:
                queryset = queryset.filter(rating__gte=int(min_rating))
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """GET /api/reviews/ - список отзывов"""
        params = request.query_params.dict()
        key = 'reviews:list:' + urlencode(sorted(params.items())) if params else 'reviews:list:all'
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        cache.set(key, serializer.data, timeout=60 * 3) 
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """GET /api/reviews/<id>/ - детали отзыва"""
        instance = self.get_object()
        key = f'review:detail:{instance.id}'
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        serializer = self.get_serializer(instance)
        cache.set(key, serializer.data, timeout=60 * 5)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """POST /api/reviews/ - создание отзыва"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        review = serializer.save(user=request.user)
        cache.delete('reviews:list:all')
        cache.delete(f'reviews:restaurant:{review.restaurant_id}:stats')
        cache.delete(f'restaurant:detail:{review.restaurant_id}')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """PUT /api/reviews/<id>/ - полное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete(f'review:detail:{instance.id}')
        cache.delete('reviews:list:all')
        cache.delete(f'reviews:restaurant:{instance.restaurant_id}:stats')
        cache.delete(f'restaurant:detail:{instance.restaurant_id}')
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/reviews/<id>/ - частичное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete(f'review:detail:{instance.id}')
        cache.delete('reviews:list:all')
        cache.delete(f'reviews:restaurant:{instance.restaurant_id}:stats')
        cache.delete(f'restaurant:detail:{instance.restaurant_id}')
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """DELETE /api/reviews/<id>/ - удаление отзыва"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        restaurant_id = instance.restaurant_id
        review_id = instance.id
        instance.delete()
        cache.delete(f'review:detail:{review_id}')
        cache.delete('reviews:list:all')
        cache.delete(f'reviews:restaurant:{restaurant_id}:stats')
        cache.delete(f'restaurant:detail:{restaurant_id}')
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """
        GET /api/reviews/my-reviews/ - отзывы текущего пользователя
        """
        queryset = Review.objects.filter(
            user=request.user
        ).select_related('user', 'restaurant', 'reservation').order_by('-created_at')
        
        serializer = ReviewListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def latest(self, request):
        """
        GET /api/reviews/latest/ - последние отзывы
        """
        queryset = Review.objects.select_related(
            'user', 'restaurant'
        ).order_by('-created_at')[:20]
        
        serializer = ReviewListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='restaurant/(?P<restaurant_id>[^/.]+)', 
            permission_classes=[permissions.AllowAny])
    def restaurant_reviews(self, request, restaurant_id=None):
        """
        GET /api/reviews/restaurant/<restaurant_id>/ - отзывы ресторана
        """
        queryset = Review.objects.filter(
            restaurant_id=restaurant_id
        ).select_related('user').order_by('-created_at')
        
        serializer = RestaurantReviewSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='restaurant/(?P<restaurant_id>[^/.]+)/stats',
            permission_classes=[permissions.AllowAny])
    def restaurant_stats(self, request, restaurant_id=None):
        """
        GET /api/reviews/restaurant/<restaurant_id>/stats/ - статистика отзывов
        """
        key = f'reviews:restaurant:{restaurant_id}:stats'
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        reviews = Review.objects.filter(restaurant_id=restaurant_id)
        
        if not reviews.exists():
            data = {
                'restaurant_id': restaurant_id,
                'total_reviews': 0,
                'average_rating': 0,
                'rating_distribution': {
                    '5': 0, '4': 0, '3': 0, '2': 0, '1': 0
                }
            }
            cache.set(key, data, timeout=60 * 10)
            return Response(data, status=status.HTTP_200_OK)
        
        stats = reviews.aggregate(
            total=Count('id'),
            average=Avg('rating')
        )
        
        distribution = {
            '5': reviews.filter(rating=5).count(),
            '4': reviews.filter(rating=4).count(),
            '3': reviews.filter(rating=3).count(),
            '2': reviews.filter(rating=2).count(),
            '1': reviews.filter(rating=1).count(),
        }
        
        data = {
            'restaurant_id': restaurant_id,
            'total_reviews': stats['total'],
            'average_rating': round(stats['average'], 2) if stats['average'] else 0,
            'rating_distribution': distribution
        }
        cache.set(key, data, timeout=60 * 10)
        return Response(data, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='restaurant/(?P<restaurant_id>[^/.]+)/can-review',
            permission_classes=[permissions.IsAuthenticated])
    def can_review(self, request, restaurant_id=None):
        """
        GET /api/reviews/restaurant/<restaurant_id>/can-review/ - проверка возможности оставить отзыв
        """
        user = request.user
        
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
