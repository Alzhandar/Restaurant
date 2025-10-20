from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError


class Review(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='user',
        help_text='User who wrote the review'
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='restaurant',
        help_text='Restaurant being reviewed'
    )
    reservation = models.OneToOneField(
        'reservations.Reservation',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='reservation',
        null=True,
        blank=True,
        help_text='Reservation this review is based on'
    )
    
    rating = models.PositiveSmallIntegerField(
        'rating',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating from 1 to 5'
    )
    comment = models.TextField(
        'comment',
        help_text='Review text'
    )
    
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    
    class Meta:
        verbose_name = 'review'
        verbose_name_plural = 'reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant']),
            models.Index(fields=['user']),
            models.Index(fields=['rating']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.restaurant.name} - {self.rating}/5"
    
    def clean(self):
        errors = {}
        
        if hasattr(self, 'user') and hasattr(self, 'restaurant'):
            from reservations.models import ReservationStatus
            
            completed_reservations = self.user.reservations.filter(
                restaurant=self.restaurant,
                status=ReservationStatus.COMPLETED
            )
            
            if not completed_reservations.exists():
                errors['__all__'] = (
                    'You can only review restaurants where you have completed reservations'
                )
        
        if hasattr(self, 'user') and hasattr(self, 'restaurant'):
            existing_review = Review.objects.filter(
                user=self.user,
                restaurant=self.restaurant
            ).exclude(pk=self.pk)
            
            if existing_review.exists():
                errors['__all__'] = 'You have already reviewed this restaurant'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new or 'rating' in kwargs.get('update_fields', []):
            self.restaurant.update_rating()

