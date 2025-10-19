"""
Admin configuration for reviews app
"""

from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    """Review admin"""
    
    list_display = ['id', 'user', 'restaurant', 'rating', 'created_at']
    list_filter = ['rating', 'restaurant', 'created_at']
    search_fields = ['user__email', 'restaurant__name', 'comment']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Review Details', {
            'fields': ('user', 'restaurant', 'reservation', 'rating', 'comment')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

