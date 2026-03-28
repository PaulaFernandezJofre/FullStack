"""
Admin de Pagos - Versión Mejorada con Mercado Pago
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Payout, PayoutOrder, Transaction, SellerEarning, PlatformRevenue, PaymentMethod


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = (
        'payout_number', 'seller_link', 'amount_formatted', 'method_badge',
        'status_badge', 'requested_at_display', 'processed_at'
    )
    list_filter = ('status', 'method', 'requested_at')
    search_fields = ('payout_number', 'seller__email')
    readonly_fields = ('id', 'payout_number', 'requested_at', 'processed_at', 'completed_at')
    actions = ['approve_payouts', 'process_payouts', 'reject_payouts']
    
    fieldsets = (
        ('Información del Pago', {
            'fields': ('id', 'payout_number', 'seller', 'status')
        }),
        ('Montos', {
            'fields': ('amount', 'currency')
        }),
        ('Método', {
            'fields': ('method', 'bank_name', 'bank_account_last4')
        }),
        ('Fechas', {
            'fields': ('requested_at', 'processed_at', 'completed_at')
        }),
        ('Notas', {
            'fields': ('notes', 'admin_notes', 'failure_reason'),
            'classes': ('collapse',)
        }),
    )
    
    def requested_at_display(self, obj):
        return obj.requested_at.strftime('%d/%m/%Y %H:%M')
    requested_at_display.short_description = 'Solicitado'
    
    def seller_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.seller.id])
        return format_html('<a href="{}">{}</a>', url, obj.seller.get_full_name() or obj.seller.email)
    seller_link.short_description = 'Vendedor'
    
    def amount_formatted(self, obj):
        return f"${obj.amount:,.0f} {obj.currency}"
    amount_formatted.short_description = 'Monto'
    
    def method_badge(self, obj):
        colors = {
            'mercadopago': '#00BFFF',
            'bank_transfer': '#00FF00',
            'paypal': '#003087',
        }
        color = colors.get(obj.method, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_method_display()
        )
    method_badge.short_description = 'Método'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'approved': '#00BFFF',
            'processing': '#9932CC',
            'completed': '#00FF00',
            'rejected': '#FF4444',
            'cancelled': '#888888',
        }
        color = colors.get(obj.status, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def approve_payouts(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='approved')
        self.message_user(request, f'{updated} retiros aprobados.')
    approve_payouts.short_description = 'Aprobar retiros seleccionados'
    
    def process_payouts(self, request, queryset):
        updated = queryset.filter(status='approved').update(
            status='processing',
            processed_at=timezone.now()
        )
        self.message_user(request, f'{updated} retiros en proceso.')
    process_payouts.short_description = 'Procesar retiros seleccionados'
    
    def reject_payouts(self, request, queryset):
        updated = queryset.filter(status__in=['pending', 'approved']).update(
            status='rejected',
            processed_at=timezone.now()
        )
        self.message_user(request, f'{updated} retiros rechazados.')
    reject_payouts.short_description = 'Rechazar retiros seleccionados'


@admin.register(PayoutOrder)
class PayoutOrderAdmin(admin.ModelAdmin):
    list_display = ('payout_link', 'order_link', 'amount')
    list_filter = ('payout__status',)
    
    def payout_link(self, obj):
        url = reverse('admin:payments_payout_change', args=[obj.payout.id])
        return format_html('<a href="{}">{}</a>', url, obj.payout.payout_number)
    payout_link.short_description = 'Retiro'
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Orden'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        'transaction_id', 'user_link', 'type_badge', 'amount_formatted',
        'status_badge', 'mp_transaction_link', 'created_at'
    )
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('id', 'user__email', 'mercadopago_payment_id', 'external_reference')
    readonly_fields = ('id', 'created_at', 'completed_at')
    
    def transaction_id(self, obj):
        return str(obj.id)[:8]
    transaction_id.short_description = 'ID'
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Usuario'
    
    def type_badge(self, obj):
        colors = {
            'sale': '#00FF00',
            'refund': '#FF4444',
            'payout': '#00BFFF',
            'deposit': '#9932CC',
            'fee': '#FFA500',
        }
        color = colors.get(obj.transaction_type, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_transaction_type_display()
        )
    type_badge.short_description = 'Tipo'
    
    def amount_formatted(self, obj):
        prefix = '-' if obj.transaction_type in ['refund', 'payout', 'fee'] else '+'
        return f"{prefix}${obj.amount:,.0f} {obj.currency}"
    amount_formatted.short_description = 'Monto'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'completed': '#00FF00',
            'failed': '#FF4444',
            'cancelled': '#888888',
        }
        color = colors.get(obj.status, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def mp_transaction_link(self, obj):
        if obj.mercadopago_payment_id:
            return format_html(
                '<span style="color: #00BFFF;">MP: {}</span>',
                obj.mercadopago_payment_id[:15] + '...' if len(obj.mercadopago_payment_id) > 15 else obj.mercadopago_payment_id
            )
        return '-'
    mp_transaction_link.short_description = 'Mercado Pago'


@admin.register(SellerEarning)
class SellerEarningAdmin(admin.ModelAdmin):
    list_display = (
        'seller_link', 'order_item_link', 'source_badge', 'gross_amount',
        'commission_display', 'net_amount', 'currency', 'created_at'
    )
    list_filter = ('source', 'currency', 'created_at')
    search_fields = ('seller__email', 'order__order_number')
    readonly_fields = ('id', 'created_at', 'payout_at')
    
    fieldsets = (
        ('Información', {
            'fields': ('id', 'seller', 'order', 'order_item', 'source', 'created_at')
        }),
        ('Montos', {
            'fields': ('gross_amount', 'commission_rate', 'commission_amount', 'net_amount', 'currency')
        }),
        ('Pagos', {
            'fields': ('is_available', 'payout', 'payout_at'),
            'classes': ('collapse',)
        }),
    )
    
    def seller_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.seller.id])
        return format_html('<a href="{}">{}</a>', url, obj.seller.get_full_name() or obj.seller.email)
    seller_link.short_description = 'Vendedor'
    
    def order_item_link(self, obj):
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
        return '-'
    order_item_link.short_description = 'Orden'
    
    def source_badge(self, obj):
        colors = {
            'sale': '#00FF00',
            'refund': '#FF4444',
            'bonus': '#9932CC',
        }
        color = colors.get(obj.source, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color, obj.get_source_display()
        )
    source_badge.short_description = 'Origen'
    
    def commission_display(self, obj):
        return f"${obj.commission_amount:,.0f} ({obj.commission_rate * 100:.0f}%)"
    commission_display.short_description = 'Comisión'


@admin.register(PlatformRevenue)
class PlatformRevenueAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'source_badge', 'order_link', 'gross_amount', 'net_amount',
        'currency', 'created_at'
    )
    list_filter = ('source', 'currency', 'created_at')
    search_fields = ('order__order_number',)
    readonly_fields = ('id', 'created_at')
    
    def source_badge(self, obj):
        colors = {
            'sale': '#00FF00',
            'subscription': '#00BFFF',
            'fee': '#FFA500',
            'other': '#888888',
        }
        color = colors.get(obj.source, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_source_display()
        )
    source_badge.short_description = 'Fuente'
    
    def order_link(self, obj):
        if obj.order:
            url = reverse('admin:orders_order_change', args=[obj.order.id])
            return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
        return '-'
    order_link.short_description = 'Orden'


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'type_badge', 'is_default', 'is_verified', 'created_at')
    list_filter = ('type', 'is_default', 'is_verified', 'created_at')
    search_fields = ('user__email',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def user_link(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Usuario'
    
    def type_badge(self, obj):
        colors = {
            'mercadopago': '#00BFFF',
            'paypal': '#003087',
            'card': '#FF4444',
            'bank_account': '#00FF00',
        }
        color = colors.get(obj.type, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 6px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_type_display()
        )
    type_badge.short_description = 'Tipo'
