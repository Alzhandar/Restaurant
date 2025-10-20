from django.contrib import admin
from .models import Reservation, ReservationStatus


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    
    list_display = ['id', 'user', 'restaurant', 'table', 'date', 'time_slot', 'guests_count', 'status', 'created_at']
    list_filter = ['status', 'date', 'restaurant', 'created_at']
    search_fields = ['user__email', 'restaurant__name', 'table__table_number']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Reservation Details', {
            'fields': ('user', 'restaurant', 'table', 'date', 'time_slot', 'guests_count')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Additional Information', {
            'fields': ('special_requests',)
        }),
        ('Tracking', {
            'fields': ('confirmation_sent', 'reminder_sent')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['confirm_reservations', 'cancel_reservations']
    
    def confirm_reservations(self, request, queryset):
        updated = queryset.update(status=ReservationStatus.CONFIRMED)
        self.message_user(request, f'{updated} reservations confirmed.')
    confirm_reservations.short_description = 'Confirm selected reservations'
    
    def cancel_reservations(self, request, queryset):
        updated = queryset.update(status=ReservationStatus.CANCELLED)
        self.message_user(request, f'{updated} reservations cancelled.')
    cancel_reservations.short_description = 'Cancel selected reservations'

