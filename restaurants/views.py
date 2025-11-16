from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from django.core.cache import cache
from django.utils.http import urlencode

from .models import Restaurant, Table, Dish
from .serializers import (
    RestaurantSerializer,
    RestaurantCreateSerializer,
    RestaurantUpdateSerializer,
    RestaurantListSerializer,
    RestaurantSearchSerializer,
    TableSerializer,
    TableCreateSerializer,
    TableMinimalSerializer,
    AvailableTablesSerializer,
    DishSerializer,
    DishCreateSerializer,
    DishUpdateSerializer,
    DishListSerializer,
    DishSearchSerializer,
    DishMinimalSerializer
)
from core.permissions import IsRestaurantOwnerOrReadOnly


class RestaurantViewSet(viewsets.GenericViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer
    permission_classes = [IsRestaurantOwnerOrReadOnly]
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'search']:
            return [permissions.AllowAny()]
        elif self.action == 'create':
            return [permissions.IsAuthenticated()]
        elif self.action == 'my_restaurants':
            return [permissions.IsAuthenticated()]
        return [IsRestaurantOwnerOrReadOnly()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RestaurantCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return RestaurantUpdateSerializer
        elif self.action == 'list':
            return RestaurantListSerializer
        elif self.action == 'search':
            return RestaurantSearchSerializer
        return RestaurantSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('owner')
        
        if self.action == 'list':
            cuisine = self.request.query_params.get('cuisine', None)
            if cuisine:
                queryset = queryset.filter(cuisine_type=cuisine)
            
            min_rating = self.request.query_params.get('min_rating', None)
            if min_rating:
                queryset = queryset.filter(average_rating__gte=float(min_rating))
            
            ordering = self.request.query_params.get('ordering', '-created_at')
            queryset = queryset.order_by(ordering)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """GET /api/restaurants/ - список ресторанов"""
        params = request.query_params.dict()
        key = 'restaurants:list:' + urlencode(sorted(params.items())) if params else 'restaurants:list:all'
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        cache.set(key, serializer.data, timeout=60 * 5) 
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """GET /api/restaurants/<id>/ - детали ресторана"""
        instance = self.get_object()
        key = f'restaurant:detail:{instance.id}'
        cached = cache.get(key)
        if cached is not None:
            return Response(cached)

        serializer = self.get_serializer(instance)
        cache.set(key, serializer.data, timeout=60 * 10)  
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """POST /api/restaurants/ - создание ресторана"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        cache.delete('restaurants:list:all')
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """PUT /api/restaurants/<id>/ - полное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        instance = self.get_object()
        cache.delete(f'restaurant:detail:{instance.id}')
        cache.delete('restaurants:list:all')
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/restaurants/<id>/ - частичное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        cache.delete(f'restaurant:detail:{instance.id}')
        cache.delete('restaurants:list:all')
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """DELETE /api/restaurants/<id>/ - удаление ресторана"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        cache.delete('restaurants:list:all')
        cache.delete(f'restaurant:detail:{instance.id}')
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def search(self, request):
        """
        GET /api/restaurants/search/?q=query - поиск ресторанов
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response([], status=status.HTTP_200_OK)
        
        queryset = Restaurant.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(address__icontains=query)
        ).select_related('owner')
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def my_restaurants(self, request):
        """
        GET /api/restaurants/my-restaurants/ - рестораны текущего пользователя
        """
        queryset = Restaurant.objects.filter(
            owner=request.user
        ).order_by('-created_at')
        
        serializer = RestaurantListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def available_tables(self, request, pk=None):
        """
        POST /api/restaurants/<id>/available-tables/ - проверка доступных столиков
        Body: {"date": "2024-01-15", "start_time": "19:00", "end_time": "21:00", "party_size": 4}
        """
        restaurant = self.get_object()
        
        serializer = AvailableTablesSerializer(
            data=request.data,
            context={'restaurant_id': restaurant.id}
        )
        serializer.is_valid(raise_exception=True)
        
        available_tables = serializer.get_available_tables()
        
        return Response({
            'restaurant_id': restaurant.id,
            'available_tables': TableMinimalSerializer(available_tables, many=True).data,
            'count': len(available_tables)
        }, status=status.HTTP_200_OK)


class TableViewSet(viewsets.GenericViewSet):
    queryset = Table.objects.all()
    serializer_class = TableSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsRestaurantOwnerOrReadOnly()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return TableCreateSerializer
        return TableSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('restaurant')
        
        restaurant_id = self.request.query_params.get('restaurant_id', None)
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """GET /api/tables/ - список столиков"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """GET /api/tables/<id>/ - детали столика"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """POST /api/tables/ - создание столика"""
        restaurant_id = request.data.get('restaurant')
        
        # Проверяем права на создание столика
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            if not (restaurant.owner == request.user or request.user.is_admin_user):
                return Response({
                    'error': 'You do not have permission to add tables to this restaurant.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'Restaurant not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """PUT /api/tables/<id>/ - полное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/tables/<id>/ - частичное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """DELETE /api/tables/<id>/ - удаление столика"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DishViewSet(viewsets.GenericViewSet):
    queryset = Dish.objects.all()
    serializer_class = DishSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'search', 'restaurant_dishes']:
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated(), IsRestaurantOwnerOrReadOnly()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DishCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DishUpdateSerializer
        elif self.action == 'list':
            return DishListSerializer
        elif self.action == 'search':
            return DishSearchSerializer
        return DishSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset().select_related('restaurant')
        
        restaurant_id = self.request.query_params.get('restaurant_id', None)
        if restaurant_id:
            queryset = queryset.filter(restaurant_id=restaurant_id)
        
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        
        min_price = self.request.query_params.get('min_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))
        
        max_price = self.request.query_params.get('max_price', None)
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))
        
        vegetarian = self.request.query_params.get('vegetarian', None)
        if vegetarian and vegetarian.lower() == 'true':
            queryset = queryset.filter(is_vegetarian=True)
        
        vegan = self.request.query_params.get('vegan', None)
        if vegan and vegan.lower() == 'true':
            queryset = queryset.filter(is_vegan=True)
        
        gluten_free = self.request.query_params.get('gluten_free', None)
        if gluten_free and gluten_free.lower() == 'true':
            queryset = queryset.filter(is_gluten_free=True)
        
        available = self.request.query_params.get('available', None)
        if available is not None:
            queryset = queryset.filter(is_available=available.lower() == 'true')
        
        ordering = self.request.query_params.get('ordering', 'name')
        queryset = queryset.order_by(ordering)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """GET /api/dishes/ - список блюд"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        """GET /api/dishes/<id>/ - детали блюда"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """POST /api/dishes/ - создание блюда"""
        restaurant_id = request.data.get('restaurant')
        
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
            if not (restaurant.owner == request.user or request.user.is_admin_user):
                return Response({
                    'error': 'You do not have permission to add dishes to this restaurant.'
                }, status=status.HTTP_403_FORBIDDEN)
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'Restaurant not found.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        serializer = self.get_serializer(data=request.data, context={'restaurant_id': restaurant_id})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """PUT /api/dishes/<id>/ - полное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def partial_update(self, request, *args, **kwargs):
        """PATCH /api/dishes/<id>/ - частичное обновление"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """DELETE /api/dishes/<id>/ - удаление блюда"""
        instance = self.get_object()
        self.check_object_permissions(request, instance)
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def search(self, request):
        """
        GET /api/dishes/search/?q=query - поиск блюд
        """
        query = request.query_params.get('q', '')
        if not query:
            return Response([], status=status.HTTP_200_OK)
        
        queryset = self.get_queryset().filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.AllowAny])
    def restaurant_dishes(self, request, pk=None):
        """
        GET /api/dishes/restaurant-dishes/<restaurant_id>/ - блюда конкретного ресторана
        """
        try:
            restaurant = Restaurant.objects.get(id=pk)
            dishes = Dish.objects.filter(restaurant=restaurant).select_related('restaurant')
            
            category = request.query_params.get('category', None)
            if category:
                dishes = dishes.filter(category=category)
            
            available = request.query_params.get('available', None)
            if available is not None:
                dishes = dishes.filter(is_available=available.lower() == 'true')
            
            serializer = DishListSerializer(dishes, many=True)
            return Response(serializer.data)
        except Restaurant.DoesNotExist:
            return Response({
                'error': 'Restaurant not found.'
            }, status=status.HTTP_404_NOT_FOUND)
