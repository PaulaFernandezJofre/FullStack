"""
Admin de Usuarios - Panel completo con verificación y gestión
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.db.models import Count, Sum

from .models import User, SellerStats, BuyerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administración completa de Usuarios con verificación."""
    
    list_display = (
        'email', 'full_name', 'role', 'status_badge', 'verification_status',
        'mercadopago_status', 'is_active', 'date_joined'
    )
    list_filter = ('role', 'status', 'is_active', 'is_staff', 'rut_verified', 'mercadopago_verified')
    search_fields = ('email', 'first_name', 'last_name', 'username', 'tax_id', 'mercadopago_email')
    ordering = ('-date_joined',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('email', 'first_name', 'last_name', 'username', 'avatar', 'bio', 'phone')
        }),
        ('Verificación - Datos Personales', {
            'fields': ('name_verified', 'password_verified', 'email_verified'),
            'classes': ('collapse',),
        }),
        ('Verificación - RUT Chile', {
            'fields': ('tax_id', 'rut_verified'),
        }),
        ('Verificación - Cuenta Bancaria', {
            'fields': ('bank_name', 'bank_account_number', 'bank_rut', 'account_verified'),
            'classes': ('collapse',),
        }),
        ('Mercado Pago', {
            'fields': ('mercadopago_email', 'mercadopago_customer_id', 'mercadopago_seller_id', 'mercadopago_verified'),
        }),
        ('Rol y Estado', {
            'fields': ('role', 'status')
        }),
        ('Permisos', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Preferencias', {
            'fields': ('language', 'currency', 'email_notifications', 'marketing_emails'),
            'classes': ('collapse',),
        }),
        ('Fechas', {
            'fields': ('last_login', 'last_login_ip', 'date_joined', 'email_verified_at')
        }),
    )
    
    add_fieldsets = (
        ('Crear Usuario', {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'role'),
        }),
    )
    
    list_editable = ('is_active',)
    list_per_page = 50
    list_max_show_all = 200
    
    actions = ['verify_selected_users', 'unverify_selected_users', 'suspend_users', 'activate_users']
    
    def status_badge(self, obj):
        colors = {
            'active': '#3ddc84',
            'pending': '#ffc107',
            'suspended': '#dc3545',
            'banned': '#6f42c1',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background: {}; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; font-weight: 600;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def verification_status(self, obj):
        checks = []
        if obj.email_verified:
            checks.append('<i class="bi bi-check-circle-fill" style="color: #3ddc84;"></i>')
        else:
            checks.append('<i class="bi bi-x-circle-fill" style="color: #dc3545;"></i>')
        
        if obj.name_verified:
            checks.append('<i class="bi bi-check-circle-fill" style="color: #3ddc84;"></i>')
        else:
            checks.append('<i class="bi bi-x-circle-fill" style="color: #dc3545;"></i>')
        
        if obj.password_verified:
            checks.append('<i class="bi bi-check-circle-fill" style="color: #3ddc84;"></i>')
        else:
            checks.append('<i class="bi bi-x-circle-fill" style="color: #dc3545;"></i>')
        
        if obj.rut_verified:
            checks.append('<i class="bi bi-check-circle-fill" style="color: #3ddc84;"></i>')
        else:
            checks.append('<i class="bi bi-x-circle-fill" style="color: #ffc107;"></i>')
        
        return format_html(
            '<span title="Email: {} | Nombre: {} | Password: {} | RUT: {}">{}</span>',
            '✓' if obj.email_verified else '✗',
            '✓' if obj.name_verified else '✗',
            '✓' if obj.password_verified else '✗',
            '✓' if obj.rut_verified else '✗',
            ''.join(checks)
        )
    verification_status.short_description = 'Verificación'
    
    def mercadopago_status(self, obj):
        if obj.mercadopago_verified:
            return format_html('<span style="color: #3ddc84;"><i class="bi bi-check-circle-fill"></i> Verificado</span>')
        elif obj.mercadopago_email:
            return format_html('<span style="color: #ffc107;"><i class="bi bi-clock-fill"></i> Pendiente</span>')
        else:
            return format_html('<span style="color: #6c757d;"><i class="bi bi-dash-circle"></i> No configurado</span>')
    mercadopago_status.short_description = 'Mercado Pago'
    
    def full_name(self, obj):
        name = obj.get_full_name()
        return name if name else '—'
    full_name.short_description = 'Nombre'
    
    @admin.action(description='Verificar usuarios seleccionados')
    def verify_selected_users(self, request, queryset):
        for user in queryset:
            user.email_verified = True
            user.name_verified = True
            user.password_verified = True
            user.rut_verified = True
            user.mercadopago_verified = True
            user.account_verified = True
            user.save()
        self.message_user(request, f'{queryset.count()} usuarios verificados.')
    
    @admin.action(description='Quitar verificación de usuarios seleccionados')
    def unverify_selected_users(self, request, queryset):
        for user in queryset:
            user.email_verified = False
            user.name_verified = False
            user.password_verified = False
            user.rut_verified = False
            user.mercadopago_verified = False
            user.account_verified = False
            user.save()
        self.message_user(request, f'{queryset.count()} usuarios sin verificar.')
    
    @admin.action(description='Suspender usuarios seleccionados')
    def suspend_users(self, request, queryset):
        queryset.update(status='suspended')
        self.message_user(request, f'{queryset.count()} usuarios suspendidos.')
    
    @admin.action(description='Activar usuarios seleccionados')
    def activate_users(self, request, queryset):
        queryset.update(status='active', is_active=True)
        self.message_user(request, f'{queryset.count()} usuarios activados.')


@admin.register(SellerStats)
class SellerStatsAdmin(admin.ModelAdmin):
    """Estadísticas detalladas de Vendedores."""
    
    list_display = (
        'user', 'seller_email', 'total_products', 'active_products',
        'total_sales', 'total_earnings', 'available_earnings', 'average_rating'
    )
    list_filter = ('updated_at',)
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('updated_at',)
    list_per_page = 25
    
    def seller_email(self, obj):
        return obj.user.email
    seller_email.short_description = 'Email'


@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    """Perfiles detallados de Compradores."""
    
    list_display = ('user', 'email', 'total_purchases', 'total_spent', 'created_date')
    list_filter = ('notify_new_products', 'notify_price_drops', 'notify_seller_news')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    list_per_page = 25
    
    def email(self, obj):
        return obj.user.email
    email.short_description = 'Email'
    
    def created_date(self, obj):
        return obj.user.date_joined.strftime('%d/%m/%Y')
    created_date.short_description = 'Desde'
