"""
Admin de Usuarios - Configuración completa del panel de administración
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SellerStats, BuyerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administración de Usuarios con roles."""
    
    list_display = ('email', 'first_name', 'last_name', 'role', 'status', 'is_active')
    list_filter = ('role', 'status', 'is_active', 'is_staff')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('email', 'first_name', 'last_name', 'username', 'avatar', 'bio')
        }),
        ('Rol y Estado', {
            'fields': ('role', 'status')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Información de Vendedor', {
            'fields': ('company_name', 'tax_id', 'website', 'mercadopago_customer_id', 'mercadopago_seller_id', 'bank_account_verified')
        }),
        ('Fechas', {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        ('Crear Usuario', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    
    list_editable = ('status', 'is_active')
    list_per_page = 25


@admin.register(SellerStats)
class SellerStatsAdmin(admin.ModelAdmin):
    """Estadísticas de Vendedores."""
    
    list_display = ('user', 'total_earnings', 'available_earnings')
    search_fields = ('user__email',)
    list_per_page = 25


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    """Perfiles de Compradores."""
    
    list_display = ('user', 'total_purchases', 'total_spent')
    search_fields = ('user__email',)
    list_per_page = 25
