"""
Custom permissions для системы бронирования.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только владельцу объекта.
    Чтение доступно всем.
    """
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Запись только владельцу
        return obj.user == request.user


class IsRestaurantOwnerOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только владельцу ресторана.
    Чтение доступно всем.
    """
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Запись только владельцу ресторана или админу
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user.is_admin_user
        
        # Для Table объектов проверяем владельца ресторана
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.owner == request.user or request.user.is_admin_user
        
        return False


class IsRestaurantOwner(permissions.BasePermission):
    """
    Разрешает доступ только владельцам ресторанов и админам.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_owner or request.user.is_admin_user
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование только администраторам.
    Чтение доступно всем.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and request.user.is_admin_user


class IsReservationParticipant(permissions.BasePermission):
    """
    Разрешает доступ к бронированию:
    - Пользователю, создавшему бронирование
    - Владельцу ресторана
    - Администратору
    """
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Владелец бронирования
        if obj.user == user:
            return True
        
        # Владелец ресторана
        if obj.restaurant.owner == user:
            return True
        
        # Администратор
        if user.is_admin_user:
            return True
        
        return False


class IsReviewAuthorOrReadOnly(permissions.BasePermission):
    """
    Разрешает редактирование отзыва только автору или администратору.
    Чтение доступно всем.
    """
    def has_object_permission(self, request, view, obj):
        # Чтение разрешено всем
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Запись только автору или админу
        return obj.user == request.user or request.user.is_admin_user
