"""
Admin configuration for restaurants app
"""

from django.contrib import admin
from .models import Restaurant, Table


class TableInline(admin.TabularInline):
    """Inline admin for tables"""
    model = Table
    extra = 1
    fields = ['table_number', 'capacity', 'location_in_restaurant', 'is_available']


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    """Restaurant admin"""
    
    list_display = ['name', 'city', 'cuisine_type', 'owner', 'average_rating', 'is_active', 'created_at']
    list_filter = ['cuisine_type', 'city', 'is_active', 'created_at']
    search_fields = ['name', 'city', 'address', 'owner__email']
    readonly_fields = ['average_rating', 'total_reviews', 'created_at', 'updated_at']
    inlines = [TableInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('owner', 'name', 'description', 'cuisine_type')
        }),
        ('Contact', {
            'fields': ('phone', 'email')
        }),
        ('Location', {
            'fields': ('address', 'city', 'latitude', 'longitude')
        }),
        ('Operating Hours', {
            'fields': ('opening_time', 'closing_time')
        }),
        ('Ratings', {
            'fields': ('average_rating', 'total_reviews')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    """Table admin"""
    
    list_display = ['restaurant', 'table_number', 'capacity', 'location_in_restaurant', 'is_available']
    list_filter = ['restaurant', 'capacity', 'location_in_restaurant', 'is_available']
    search_fields = ['restaurant__name', 'table_number']
    readonly_fields = ['created_at', 'updated_at']

