"""
Permissions de Producto
"""

from rest_framework import permissions


class IsOwnerOrSeller(permissions.BasePermission):
    """Permite acceso solo al dueño del producto."""
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.seller == request.user or request.user.is_staff


class IsApprovedProduct(permissions.BasePermission):
    """Permite acceso solo a productos aprobados."""
    
    def has_object_permission(self, request, view, obj):
        return obj.status == 'approved' or request.user.is_staff
