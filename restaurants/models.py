"""
Restaurant and Table models for Restaurant Reservation System
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from phonenumber_field.modelfields import PhoneNumberField


class CuisineType(models.TextChoices):
    """Types of cuisine"""
    ITALIAN = 'italian', 'Итальянская'
    JAPANESE = 'japanese', 'Японская'
    CHINESE = 'chinese', 'Китайская'
    FRENCH = 'french', 'Французская'
    MEXICAN = 'mexican', 'Мексиканская'
    INDIAN = 'indian', 'Индийская'
    THAI = 'thai', 'Тайская'
    AMERICAN = 'american', 'Американская'
    MEDITERRANEAN = 'mediterranean', 'Средиземноморская'
    RUSSIAN = 'russian', 'Русская'
    GEORGIAN = 'georgian', 'Грузинская'
    OTHER = 'other', 'Другая'


class Restaurant(models.Model):
    """
    Restaurant model
    
    Represents a restaurant in the system.
    Each restaurant has an owner, location, and operating hours.
    """
    
    # Owner
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_restaurants',
        verbose_name='owner',
        help_text='Restaurant owner'
    )
    
    # Basic Information
    name = models.CharField(
        'name',
        max_length=200,
        help_text='Restaurant name'
    )
    description = models.TextField(
        'description',
        blank=True,
        help_text='Restaurant description'
    )
    cuisine_type = models.CharField(
        'cuisine type',
        max_length=20,
        choices=CuisineType.choices,
        help_text='Type of cuisine'
    )
    
    # Contact Information
    phone = PhoneNumberField(
        'phone number',
        help_text='Contact phone number'
    )
    email = models.EmailField(
        'email',
        help_text='Contact email'
    )
    
    # Location
    address = models.CharField(
        'address',
        max_length=500,
        help_text='Full address'
    )
    city = models.CharField(
        'city',
        max_length=100,
        help_text='City'
    )
    latitude = models.DecimalField(
        'latitude',
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-90), MaxValueValidator(90)],
        help_text='Latitude coordinate'
    )
    longitude = models.DecimalField(
        'longitude',
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        validators=[MinValueValidator(-180), MaxValueValidator(180)],
        help_text='Longitude coordinate'
    )
    
    # Operating Hours
    opening_time = models.TimeField(
        'opening time',
        help_text='Restaurant opening time'
    )
    closing_time = models.TimeField(
        'closing time',
        help_text='Restaurant closing time'
    )
    
    # Ratings
    average_rating = models.DecimalField(
        'average rating',
        max_digits=3,
        decimal_places=2,
        default=0.0,
        validators=[MinValueValidator(0), MaxValueValidator(5)],
        help_text='Average rating (0-5)'
    )
    total_reviews = models.PositiveIntegerField(
        'total reviews',
        default=0,
        help_text='Total number of reviews'
    )
    
    # Status
    is_active = models.BooleanField(
        'active',
        default=True,
        help_text='Is restaurant active and accepting reservations'
    )
    
    # Timestamps
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    
    class Meta:
        verbose_name = 'restaurant'
        verbose_name_plural = 'restaurants'
        ordering = ['-average_rating', 'name']
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['cuisine_type']),
            models.Index(fields=['owner']),
            models.Index(fields=['average_rating']),
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.city})"
    
    def update_rating(self):
        """Update average rating based on reviews"""
        from reviews.models import Review
        
        reviews = Review.objects.filter(restaurant=self)
        self.total_reviews = reviews.count()
        
        if self.total_reviews > 0:
            total_rating = sum(review.rating for review in reviews)
            self.average_rating = total_rating / self.total_reviews
        else:
            self.average_rating = 0.0
        
        self.save(update_fields=['average_rating', 'total_reviews'])


class TableLocation(models.TextChoices):
    """Location of table in restaurant"""
    MAIN_HALL = 'main_hall', 'Основной зал'
    TERRACE = 'terrace', 'Терраса'
    VIP_ROOM = 'vip_room', 'VIP зал'
    BAR = 'bar', 'Барная зона'
    WINDOW = 'window', 'У окна'


class Table(models.Model):
    """
    Table model
    
    Represents a table in a restaurant.
    Tables have capacity and location within the restaurant.
    """
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='tables',
        verbose_name='restaurant',
        help_text='Restaurant this table belongs to'
    )
    
    table_number = models.CharField(
        'table number',
        max_length=20,
        help_text='Table number or identifier'
    )
    
    capacity = models.PositiveSmallIntegerField(
        'capacity',
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text='Maximum number of guests'
    )
    
    location_in_restaurant = models.CharField(
        'location',
        max_length=20,
        choices=TableLocation.choices,
        default=TableLocation.MAIN_HALL,
        help_text='Location of table in restaurant'
    )
    
    is_available = models.BooleanField(
        'available',
        default=True,
        help_text='Is table available for reservations'
    )
    
    # Timestamps
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    
    class Meta:
        verbose_name = 'table'
        verbose_name_plural = 'tables'
        ordering = ['restaurant', 'table_number']
        unique_together = [['restaurant', 'table_number']]
        indexes = [
            models.Index(fields=['restaurant']),
            models.Index(fields=['capacity']),
            models.Index(fields=['is_available']),
        ]
    
    def __str__(self):
        return f"{self.restaurant.name} - Table {self.table_number} ({self.capacity} seats)"

