from django.contrib import admin
from .models import Restaurant, Table, Dish


class TableInline(admin.TabularInline):
    model = Table
    extra = 1
    fields = ['table_number', 'capacity', 'location_in_restaurant', 'is_available']


class DishInline(admin.TabularInline):
    model = Dish
    extra = 1
    fields = ['name', 'category', 'price', 'is_available']


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):    
    list_display = ['name', 'city', 'cuisine_type', 'owner', 'average_rating', 'is_active', 'created_at']
    list_filter = ['cuisine_type', 'city', 'is_active', 'created_at']
    search_fields = ['name', 'city', 'address', 'owner__email']
    readonly_fields = ['average_rating', 'total_reviews', 'created_at', 'updated_at']
    inlines = [TableInline, DishInline]
    
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
    list_display = ['restaurant', 'table_number', 'capacity', 'location_in_restaurant', 'is_available']
    list_filter = ['restaurant', 'capacity', 'location_in_restaurant', 'is_available']
    search_fields = ['restaurant__name', 'table_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ['name', 'restaurant', 'category', 'price', 'is_available', 'created_at']
    list_filter = ['category', 'is_available', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_spicy', 'created_at']
    search_fields = ['name', 'description', 'restaurant__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('restaurant', 'name', 'description', 'category')
        }),
        ('Pricing', {
            'fields': ('price', 'preparation_time')
        }),
        ('Dietary Information', {
            'fields': ('is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_spicy')
        }),
        ('Availability', {
            'fields': ('is_available',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

