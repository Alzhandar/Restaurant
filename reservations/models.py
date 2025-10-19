"""
Reservation models for Restaurant Reservation System
"""

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator


class ReservationStatus(models.TextChoices):
    """Reservation status"""
    PENDING = 'pending', 'Ожидает подтверждения'
    CONFIRMED = 'confirmed', 'Подтверждено'
    SEATED = 'seated', 'Гость за столом'
    COMPLETED = 'completed', 'Завершено'
    CANCELLED = 'cancelled', 'Отменено'
    NO_SHOW = 'no_show', 'Гость не пришёл'


class Reservation(models.Model):
    """
    Reservation model
    
    Represents a table reservation in a restaurant.
    Includes validation for date/time and guest count.
    """
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='user',
        help_text='User who made the reservation'
    )
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='restaurant',
        help_text='Restaurant for reservation'
    )
    table = models.ForeignKey(
        'restaurants.Table',
        on_delete=models.CASCADE,
        related_name='reservations',
        verbose_name='table',
        help_text='Reserved table'
    )
    
    # Reservation Details
    date = models.DateField(
        'date',
        help_text='Reservation date'
    )
    time_slot = models.TimeField(
        'time',
        help_text='Reservation time'
    )
    guests_count = models.PositiveSmallIntegerField(
        'guests count',
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text='Number of guests'
    )
    
    # Status
    status = models.CharField(
        'status',
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.PENDING,
        help_text='Reservation status'
    )
    
    # Additional Information
    special_requests = models.TextField(
        'special requests',
        blank=True,
        help_text='Special requests from guest (allergies, celebration, etc.)'
    )
    
    # Tracking flags
    confirmation_sent = models.BooleanField(
        'confirmation sent',
        default=False,
        help_text='Was confirmation email sent'
    )
    reminder_sent = models.BooleanField(
        'reminder sent',
        default=False,
        help_text='Was reminder email sent'
    )
    
    # Timestamps
    created_at = models.DateTimeField('created at', auto_now_add=True)
    updated_at = models.DateTimeField('updated at', auto_now=True)
    
    class Meta:
        verbose_name = 'reservation'
        verbose_name_plural = 'reservations'
        ordering = ['-date', '-time_slot']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['restaurant']),
            models.Index(fields=['table']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['date', 'time_slot']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.restaurant.name} - {self.date} {self.time_slot} - {self.user.email}"
    
    def clean(self):
        """Validate reservation data"""
        errors = {}
        
        # Check date is not in the past
        if self.date and self.date < timezone.now().date():
            errors['date'] = 'Reservation date cannot be in the past'
        
        # Check time is within restaurant operating hours
        if self.time_slot and hasattr(self, 'restaurant'):
            if (self.time_slot < self.restaurant.opening_time or 
                self.time_slot >= self.restaurant.closing_time):
                errors['time_slot'] = (
                    f'Reservation time must be between {self.restaurant.opening_time} '
                    f'and {self.restaurant.closing_time}'
                )
        
        # Check guests count does not exceed table capacity
        if self.guests_count and hasattr(self, 'table'):
            if self.guests_count > self.table.capacity:
                errors['guests_count'] = (
                    f'Number of guests ({self.guests_count}) exceeds '
                    f'table capacity ({self.table.capacity})'
                )
        
        # Check table belongs to the restaurant
        if hasattr(self, 'table') and hasattr(self, 'restaurant'):
            if self.table.restaurant_id != self.restaurant_id:
                errors['table'] = 'Selected table does not belong to this restaurant'
        
        # Check table is available
        if hasattr(self, 'table') and not self.table.is_available:
            errors['table'] = 'Selected table is not available'
        
        # Check restaurant is active
        if hasattr(self, 'restaurant') and not self.restaurant.is_active:
            errors['restaurant'] = 'This restaurant is not accepting reservations'
        
        # Check for conflicting reservations (same table, overlapping time)
        if (self.date and self.time_slot and hasattr(self, 'table')):
            conflicting = Reservation.objects.filter(
                table=self.table,
                date=self.date,
                time_slot=self.time_slot,
                status__in=[
                    ReservationStatus.PENDING,
                    ReservationStatus.CONFIRMED,
                    ReservationStatus.SEATED
                ]
            ).exclude(pk=self.pk)
            
            if conflicting.exists():
                errors['__all__'] = 'This table is already reserved for this time slot'
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        super().save(*args, **kwargs)
    
    def confirm(self):
        """Confirm reservation"""
        self.status = ReservationStatus.CONFIRMED
        self.save(update_fields=['status', 'updated_at'])
    
    def seat(self):
        """Mark guest as seated"""
        self.status = ReservationStatus.SEATED
        self.save(update_fields=['status', 'updated_at'])
    
    def complete(self):
        """Complete reservation"""
        self.status = ReservationStatus.COMPLETED
        self.save(update_fields=['status', 'updated_at'])
    
    def cancel(self):
        """Cancel reservation"""
        self.status = ReservationStatus.CANCELLED
        self.save(update_fields=['status', 'updated_at'])
    
    def mark_no_show(self):
        """Mark as no-show"""
        self.status = ReservationStatus.NO_SHOW
        self.save(update_fields=['status', 'updated_at'])
    
    @property
    def is_past(self):
        """Check if reservation is in the past"""
        return self.date < timezone.now().date()
    
    @property
    def is_today(self):
        """Check if reservation is today"""
        return self.date == timezone.now().date()
    
    @property
    def is_active(self):
        """Check if reservation is active"""
        return self.status in [
            ReservationStatus.PENDING,
            ReservationStatus.CONFIRMED,
            ReservationStatus.SEATED
        ]

