"""
Permissions de Usuario
"""

from rest_framework import permissions


class IsOwnerOrAdmin(permissions.BasePermission):
    """Permite acceso solo al dueño o admin."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj == request.user or request.user.is_staff


class IsSeller(permissions.BasePermission):
    """Permite acceso solo a vendedores."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.can_sell


class IsAdmin(permissions.BasePermission):
    """Permite acceso solo a administradores."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin
