"""
Serializers for restaurants app
"""

from rest_framework import serializers
from .models import Restaurant, Table, Dish, CuisineType, TableLocation, DishCategory
from users.serializers import UserMinimalSerializer


class TableSerializer(serializers.ModelSerializer):
    """Serializer for Table model"""
    
    class Meta:
        model = Table
        fields = [
            'id', 'restaurant', 'table_number', 'capacity',
            'location_in_restaurant', 'is_available', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_capacity(self, value):
        """Validate capacity is positive"""
        if value < 1:
            raise serializers.ValidationError("Capacity must be at least 1")
        if value > 20:
            raise serializers.ValidationError("Capacity cannot exceed 20")
        return value


class TableMinimalSerializer(serializers.ModelSerializer):
    """Minimal table info for nested serializers"""
    
    class Meta:
        model = Table
        fields = ['id', 'table_number', 'capacity', 'location_in_restaurant']
        read_only_fields = ['id']


class RestaurantSerializer(serializers.ModelSerializer):
    """Serializer for Restaurant model"""
    
    owner = UserMinimalSerializer(read_only=True)
    tables = TableMinimalSerializer(many=True, read_only=True)
    tables_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'owner', 'name', 'description', 'cuisine_type',
            'phone', 'email', 'address', 'city',
            'latitude', 'longitude',
            'opening_time', 'closing_time',
            'average_rating', 'total_reviews',
            'is_active', 'tables', 'tables_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner', 'average_rating', 'total_reviews',
            'created_at', 'updated_at'
        ]
    
    def get_tables_count(self, obj):
        """Get total number of tables"""
        return obj.tables.count()
    
    def validate(self, attrs):
        """Validate restaurant data"""
        # Validate opening and closing times
        if 'opening_time' in attrs and 'closing_time' in attrs:
            if attrs['opening_time'] >= attrs['closing_time']:
                raise serializers.ValidationError({
                    'closing_time': 'Closing time must be after opening time'
                })
        
        # Validate coordinates
        if 'latitude' in attrs and attrs['latitude']:
            if not (-90 <= attrs['latitude'] <= 90):
                raise serializers.ValidationError({
                    'latitude': 'Latitude must be between -90 and 90'
                })
        
        if 'longitude' in attrs and attrs['longitude']:
            if not (-180 <= attrs['longitude'] <= 180):
                raise serializers.ValidationError({
                    'longitude': 'Longitude must be between -180 and 180'
                })
        
        return attrs
    
    def create(self, validated_data):
        """Create restaurant with owner from request"""
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class RestaurantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a restaurant"""
    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'cuisine_type',
            'phone', 'email', 'address', 'city',
            'latitude', 'longitude',
            'opening_time', 'closing_time'
        ]
    
    def validate(self, attrs):
        """Validate restaurant data"""
        if attrs['opening_time'] >= attrs['closing_time']:
            raise serializers.ValidationError({
                'closing_time': 'Closing time must be after opening time'
            })
        return attrs
    
    def create(self, validated_data):
        """Create restaurant with owner from request"""
        validated_data['owner'] = self.context['request'].user
        return Restaurant.objects.create(**validated_data)


class RestaurantUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a restaurant"""
    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'cuisine_type',
            'phone', 'email', 'address', 'city',
            'latitude', 'longitude',
            'opening_time', 'closing_time', 'is_active'
        ]


class RestaurantListSerializer(serializers.ModelSerializer):
    """Minimal serializer for restaurant list"""
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'cuisine_type', 'city',
            'average_rating', 'total_reviews',
            'opening_time', 'closing_time', 'is_active'
        ]
        read_only_fields = ['id']


class RestaurantSearchSerializer(serializers.ModelSerializer):
    """Serializer for restaurant search results"""
    
    distance = serializers.FloatField(read_only=True, required=False)
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'cuisine_type', 'city', 'address',
            'average_rating', 'total_reviews',
            'latitude', 'longitude', 'distance'
        ]
        read_only_fields = ['id']


class TableCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a table"""
    
    class Meta:
        model = Table
        fields = ['table_number', 'capacity', 'location_in_restaurant']
    
    def validate_capacity(self, value):
        """Validate capacity"""
        if value < 1 or value > 20:
            raise serializers.ValidationError("Capacity must be between 1 and 20")
        return value
    
    def create(self, validated_data):
        """Create table with restaurant from context"""
        validated_data['restaurant_id'] = self.context['restaurant_id']
        return Table.objects.create(**validated_data)


class AvailableTablesSerializer(serializers.Serializer):
    """Serializer for checking available tables"""
    
    date = serializers.DateField(required=True)
    time_slot = serializers.TimeField(required=True)
    guests_count = serializers.IntegerField(required=True, min_value=1, max_value=20)
    
    def validate(self, attrs):
        """Validate availability check params"""
        from django.utils import timezone
        
        # Check date is not in the past
        if attrs['date'] < timezone.now().date():
            raise serializers.ValidationError({
                'date': 'Date cannot be in the past'
            })
        
        return attrs


class DishSerializer(serializers.ModelSerializer):
    """Serializer for Dish model"""
    
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Dish
        fields = [
            'id', 'restaurant', 'restaurant_name', 'name', 'description',
            'category', 'price', 'preparation_time',
            'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_spicy',
            'is_available', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def validate_preparation_time(self, value):
        """Validate preparation time"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Preparation time must be positive")
        return value


class DishMinimalSerializer(serializers.ModelSerializer):
    """Minimal dish info for nested serializers"""
    
    class Meta:
        model = Dish
        fields = ['id', 'name', 'price', 'category', 'is_available']
        read_only_fields = ['id']


class DishCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a dish"""
    
    class Meta:
        model = Dish
        fields = [
            'name', 'description', 'category', 'price',
            'preparation_time', 'is_vegetarian', 'is_vegan',
            'is_gluten_free', 'is_spicy', 'is_available'
        ]
    
    def validate_price(self, value):
        """Validate price"""
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def validate_preparation_time(self, value):
        """Validate preparation time"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Preparation time must be positive")
        return value
    
    def create(self, validated_data):
        """Create dish with restaurant from context"""
        validated_data['restaurant_id'] = self.context['restaurant_id']
        return Dish.objects.create(**validated_data)


class DishUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating a dish"""
    
    class Meta:
        model = Dish
        fields = [
            'name', 'description', 'category', 'price',
            'preparation_time', 'is_vegetarian', 'is_vegan',
            'is_gluten_free', 'is_spicy', 'is_available'
        ]
    
    def validate_price(self, value):
        """Validate price"""
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def validate_preparation_time(self, value):
        """Validate preparation time"""
        if value is not None and value < 0:
            raise serializers.ValidationError("Preparation time must be positive")
        return value


class DishListSerializer(serializers.ModelSerializer):
    """Minimal serializer for dish list"""
    
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'restaurant_name', 'category', 'price',
            'is_vegetarian', 'is_vegan', 'is_available'
        ]
        read_only_fields = ['id']


class DishSearchSerializer(serializers.ModelSerializer):
    """Serializer for dish search results"""
    
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    restaurant_city = serializers.CharField(source='restaurant.city', read_only=True)
    
    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'description', 'category', 'price',
            'restaurant_name', 'restaurant_city',
            'is_vegetarian', 'is_vegan', 'is_available'
        ]
        read_only_fields = ['id']
