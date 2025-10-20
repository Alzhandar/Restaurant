from rest_framework import serializers
from django.utils import timezone
from .models import Reservation, ReservationStatus
from users.serializers import UserMinimalSerializer
from restaurants.serializers import RestaurantListSerializer, TableMinimalSerializer


class ReservationSerializer(serializers.ModelSerializer):    
    user = UserMinimalSerializer(read_only=True)
    restaurant = RestaurantListSerializer(read_only=True)
    table = TableMinimalSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'user', 'restaurant', 'table',
            'date', 'time_slot', 'guests_count',
            'status', 'status_display',
            'special_requests',
            'confirmation_sent', 'reminder_sent',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'confirmation_sent',
            'reminder_sent', 'created_at', 'updated_at'
        ]


class ReservationCreateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Reservation
        fields = [
            'restaurant', 'table', 'date', 'time_slot',
            'guests_count', 'special_requests'
        ]
    
    def validate(self, attrs):
        if attrs['date'] < timezone.now().date():
            raise serializers.ValidationError({
                'date': 'Reservation date cannot be in the past'
            })
        
        restaurant = attrs['restaurant']
        time_slot = attrs['time_slot']
        
        if time_slot < restaurant.opening_time or time_slot >= restaurant.closing_time:
            raise serializers.ValidationError({
                'time_slot': f'Reservation time must be between {restaurant.opening_time} and {restaurant.closing_time}'
            })
        
        table = attrs['table']
        guests_count = attrs['guests_count']
        
        if guests_count > table.capacity:
            raise serializers.ValidationError({
                'guests_count': f'Number of guests ({guests_count}) exceeds table capacity ({table.capacity})'
            })
        
        if table.restaurant_id != restaurant.id:
            raise serializers.ValidationError({
                'table': 'Selected table does not belong to this restaurant'
            })
        
        if not table.is_available:
            raise serializers.ValidationError({
                'table': 'Selected table is not available'
            })
        
        if not restaurant.is_active:
            raise serializers.ValidationError({
                'restaurant': 'This restaurant is not accepting reservations'
            })
        
        conflicting = Reservation.objects.filter(
            table=table,
            date=attrs['date'],
            time_slot=time_slot,
            status__in=[
                ReservationStatus.PENDING,
                ReservationStatus.CONFIRMED,
                ReservationStatus.SEATED
            ]
        )
        
        if conflicting.exists():
            raise serializers.ValidationError({
                'table': 'This table is already reserved for this time slot'
            })
        
        return attrs
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['status'] = ReservationStatus.PENDING
        return Reservation.objects.create(**validated_data)


class ReservationUpdateSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Reservation
        fields = ['date', 'time_slot', 'guests_count', 'special_requests']
    
    def validate(self, attrs):
        instance = self.instance
        
        date = attrs.get('date', instance.date)
        time_slot = attrs.get('time_slot', instance.time_slot)
        guests_count = attrs.get('guests_count', instance.guests_count)
        
        if date < timezone.now().date():
            raise serializers.ValidationError({
                'date': 'Reservation date cannot be in the past'
            })
        
        if time_slot < instance.restaurant.opening_time or time_slot >= instance.restaurant.closing_time:
            raise serializers.ValidationError({
                'time_slot': f'Reservation time must be between {instance.restaurant.opening_time} and {instance.restaurant.closing_time}'
            })
        
        if guests_count > instance.table.capacity:
            raise serializers.ValidationError({
                'guests_count': f'Number of guests ({guests_count}) exceeds table capacity ({instance.table.capacity})'
            })
        
        conflicting = Reservation.objects.filter(
            table=instance.table,
            date=date,
            time_slot=time_slot,
            status__in=[
                ReservationStatus.PENDING,
                ReservationStatus.CONFIRMED,
                ReservationStatus.SEATED
            ]
        ).exclude(pk=instance.pk)
        
        if conflicting.exists():
            raise serializers.ValidationError({
                'time_slot': 'This table is already reserved for this time slot'
            })
        
        return attrs


class ReservationListSerializer(serializers.ModelSerializer):    
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    table_number = serializers.CharField(source='table.table_number', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Reservation
        fields = [
            'id', 'user_name', 'restaurant_name', 'table_number',
            'date', 'time_slot', 'guests_count',
            'status', 'status_display', 'created_at'
        ]
        read_only_fields = ['id']


class ReservationStatusUpdateSerializer(serializers.Serializer):    
    status = serializers.ChoiceField(choices=ReservationStatus.choices)
    
    def validate_status(self, value):
        instance = self.context.get('reservation')
        current_status = instance.status
        
        allowed_transitions = {
            ReservationStatus.PENDING: [ReservationStatus.CONFIRMED, ReservationStatus.CANCELLED],
            ReservationStatus.CONFIRMED: [ReservationStatus.SEATED, ReservationStatus.CANCELLED, ReservationStatus.NO_SHOW],
            ReservationStatus.SEATED: [ReservationStatus.COMPLETED, ReservationStatus.CANCELLED],
            ReservationStatus.COMPLETED: [],
            ReservationStatus.CANCELLED: [],
            ReservationStatus.NO_SHOW: [],
        }
        
        if value not in allowed_transitions.get(current_status, []):
            raise serializers.ValidationError(
                f"Cannot change status from {current_status} to {value}"
            )
        
        return value
    
    def save(self):
        instance = self.context['reservation']
        status = self.validated_data['status']
        
        if status == ReservationStatus.CONFIRMED:
            instance.confirm()
        elif status == ReservationStatus.SEATED:
            instance.seat()
        elif status == ReservationStatus.COMPLETED:
            instance.complete()
        elif status == ReservationStatus.CANCELLED:
            instance.cancel()
        elif status == ReservationStatus.NO_SHOW:
            instance.mark_no_show()
        
        return instance


class ReservationMinimalSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Reservation
        fields = ['id', 'date', 'time_slot', 'status']
        read_only_fields = ['id']
