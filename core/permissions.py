from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user


class IsRestaurantOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        if hasattr(obj, 'owner'):
            return obj.owner == request.user or request.user.is_admin_user
        
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.owner == request.user or request.user.is_admin_user
        
        return False


class IsRestaurantOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.is_owner or request.user.is_admin_user
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_authenticated and request.user.is_admin_user


class IsReservationParticipant(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if obj.user == user:
            return True
        
        if obj.restaurant.owner == user:
            return True
        
        if user.is_admin_user:
            return True
        
        return False


class IsReviewAuthorOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user or request.user.is_admin_user
