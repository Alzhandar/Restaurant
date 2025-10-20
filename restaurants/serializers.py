from rest_framework import serializers
from .models import Restaurant, Table, Dish, CuisineType, TableLocation, DishCategory
from users.serializers import UserMinimalSerializer


class TableSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Table
        fields = [
            'id', 'restaurant', 'table_number', 'capacity',
            'location_in_restaurant', 'is_available', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def validate_capacity(self, value):
        if value < 1:
            raise serializers.ValidationError("Capacity must be at least 1")
        if value > 20:
            raise serializers.ValidationError("Capacity cannot exceed 20")
        return value


class TableMinimalSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Table
        fields = ['id', 'table_number', 'capacity', 'location_in_restaurant']
        read_only_fields = ['id']


class RestaurantSerializer(serializers.ModelSerializer):    
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
        return obj.tables.count()
    
    def validate(self, attrs):
        if 'opening_time' in attrs and 'closing_time' in attrs:
            if attrs['opening_time'] >= attrs['closing_time']:
                raise serializers.ValidationError({
                    'closing_time': 'Closing time must be after opening time'
                })
        
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
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)


class RestaurantCreateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'cuisine_type',
            'phone', 'email', 'address', 'city',
            'latitude', 'longitude',
            'opening_time', 'closing_time'
        ]
    
    def validate(self, attrs):
        if attrs['opening_time'] >= attrs['closing_time']:
            raise serializers.ValidationError({
                'closing_time': 'Closing time must be after opening time'
            })
        return attrs
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return Restaurant.objects.create(**validated_data)


class RestaurantUpdateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'cuisine_type',
            'phone', 'email', 'address', 'city',
            'latitude', 'longitude',
            'opening_time', 'closing_time', 'is_active'
        ]


class RestaurantListSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'cuisine_type', 'city',
            'average_rating', 'total_reviews',
            'opening_time', 'closing_time', 'is_active'
        ]
        read_only_fields = ['id']


class RestaurantSearchSerializer(serializers.ModelSerializer):    
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
    class Meta:
        model = Table
        fields = ['table_number', 'capacity', 'location_in_restaurant']
    
    def validate_capacity(self, value):
        if value < 1 or value > 20:
            raise serializers.ValidationError("Capacity must be between 1 and 20")
        return value
    
    def create(self, validated_data):
        validated_data['restaurant_id'] = self.context['restaurant_id']
        return Table.objects.create(**validated_data)


class AvailableTablesSerializer(serializers.Serializer):    
    date = serializers.DateField(required=True)
    time_slot = serializers.TimeField(required=True)
    guests_count = serializers.IntegerField(required=True, min_value=1, max_value=20)
    
    def validate(self, attrs):
        from django.utils import timezone
        if attrs['date'] < timezone.now().date():
            raise serializers.ValidationError({
                'date': 'Date cannot be in the past'
            })
        
        return attrs


class DishSerializer(serializers.ModelSerializer):    
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
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def validate_preparation_time(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Preparation time must be positive")
        return value


class DishMinimalSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Dish
        fields = ['id', 'name', 'price', 'category', 'is_available']
        read_only_fields = ['id']


class DishCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = [
            'name', 'description', 'category', 'price',
            'preparation_time', 'is_vegetarian', 'is_vegan',
            'is_gluten_free', 'is_spicy', 'is_available'
        ]
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def validate_preparation_time(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Preparation time must be positive")
        return value
    
    def create(self, validated_data):
        validated_data['restaurant_id'] = self.context['restaurant_id']
        return Dish.objects.create(**validated_data)


class DishUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Dish
        fields = [
            'name', 'description', 'category', 'price',
            'preparation_time', 'is_vegetarian', 'is_vegan',
            'is_gluten_free', 'is_spicy', 'is_available'
        ]
    
    def validate_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Price must be positive")
        return value
    
    def validate_preparation_time(self, value):
        if value is not None and value < 0:
            raise serializers.ValidationError("Preparation time must be positive")
        return value


class DishListSerializer(serializers.ModelSerializer):    
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'restaurant_name', 'category', 'price',
            'is_vegetarian', 'is_vegan', 'is_available'
        ]
        read_only_fields = ['id']


class DishSearchSerializer(serializers.ModelSerializer):    
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
