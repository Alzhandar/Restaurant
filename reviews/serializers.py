from rest_framework import serializers
from .models import Review
from users.serializers import UserMinimalSerializer
from restaurants.serializers import RestaurantListSerializer
from reservations.models import ReservationStatus


class ReviewSerializer(serializers.ModelSerializer):    
    user = UserMinimalSerializer(read_only=True)
    restaurant = RestaurantListSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user', 'restaurant', 'reservation',
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['restaurant', 'reservation', 'rating', 'comment']
    
    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value
    
    def validate(self, attrs):
        user = self.context['request'].user
        restaurant = attrs['restaurant']
        
        completed_reservations = user.reservations.filter(
            restaurant=restaurant,
            status=ReservationStatus.COMPLETED
        )
        
        if not completed_reservations.exists():
            raise serializers.ValidationError({
                'restaurant': 'You can only review restaurants where you have completed reservations'
            })
        
        if 'reservation' in attrs and attrs['reservation']:
            reservation = attrs['reservation']
            
            if reservation.user != user:
                raise serializers.ValidationError({
                    'reservation': 'This reservation does not belong to you'
                })
            
            if reservation.restaurant != restaurant:
                raise serializers.ValidationError({
                    'reservation': 'This reservation is not for the selected restaurant'
                })
            
            if reservation.status != ReservationStatus.COMPLETED:
                raise serializers.ValidationError({
                    'reservation': 'You can only review completed reservations'
                })
            
            if hasattr(reservation, 'review'):
                raise serializers.ValidationError({
                    'reservation': 'You have already reviewed this reservation'
                })
        
        existing_review = Review.objects.filter(
            user=user,
            restaurant=restaurant
        )
        
        if existing_review.exists():
            raise serializers.ValidationError({
                'restaurant': 'You have already reviewed this restaurant'
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return Review.objects.create(**validated_data)


class ReviewUpdateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Review
        fields = ['rating', 'comment']
    
    def validate_rating(self, value):
        if not (1 <= value <= 5):
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class ReviewListSerializer(serializers.ModelSerializer):    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'user_name', 'restaurant_name',
            'rating', 'comment', 'created_at'
        ]
        read_only_fields = ['id']


class RestaurantReviewSerializer(serializers.ModelSerializer):    
    user = UserMinimalSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id']


class ReviewStatsSerializer(serializers.Serializer):    
    total_reviews = serializers.IntegerField()
    average_rating = serializers.FloatField()
    rating_distribution = serializers.DictField()
    
    five_star = serializers.IntegerField(required=False)
    four_star = serializers.IntegerField(required=False)
    three_star = serializers.IntegerField(required=False)
    two_star = serializers.IntegerField(required=False)
    one_star = serializers.IntegerField(required=False)
