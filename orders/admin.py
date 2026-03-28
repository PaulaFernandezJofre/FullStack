"""
Admin de Pedidos y Carritos - Versión Mejorada
"""

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Cart, CartItem, Order, OrderItem, ProductDownload, Coupon, Refund


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'items_count', 'subtotal', 'created_at', 'expires_at')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('user__email', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def items_count(self, obj):
        return obj.items_count
    items_count.short_description = 'Items'
    
    def subtotal(self, obj):
        from django.conf import settings
        return f"{settings.CURRENCY_SYMBOL}{obj.subtotal:,.2f}"
    subtotal.short_description = 'Subtotal'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'license_type', 'quantity', 'subtotal')
    list_filter = ('license_type', 'created_at')
    search_fields = ('product__name', 'cart__user__email')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'order_number', 'buyer', 'status_badge', 'payment_status',
        'total_formatted', 'iva_display', 'seller_earnings_display',
        'created_at', 'paid_at'
    )
    list_filter = ('status', 'payment_method', 'created_at', 'paid_at')
    search_fields = ('order_number', 'buyer__email', 'buyer__first_name', 'mercadopago_payment_id')
    readonly_fields = (
        'id', 'order_number', 'created_at', 'updated_at', 'paid_at',
        'completed_at', 'cancelled_at', 'subtotal', 'total',
        'iva_amount', 'mercadopago_fee', 'platform_maintenance', 'seller_total'
    )
    fieldsets = (
        ('Información de Orden', {
            'fields': ('id', 'order_number', 'buyer', 'status', 'created_at')
        }),
        ('Contacto', {
            'fields': ('email', 'phone')
        }),
        ('Estado del Pago', {
            'fields': ('payment_method', 'mercadopago_payment_id', 'mercadopago_merchant_order_id', 'paid_at')
        }),
        ('Montos', {
            'fields': ('subtotal', 'discount', 'total', 'currency')
        }),
        ('Distribución Financiera', {
            'fields': ('iva_amount', 'mercadopago_fee', 'platform_maintenance', 'seller_total'),
            'classes': ('collapse',)
        }),
        ('Notas', {
            'fields': ('notes', 'admin_notes'),
            'classes': ('collapse',)
        }),
    )
    actions = ['export_to_pdf', 'mark_as_completed', 'mark_as_cancelled']
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'paid': '#00BFFF',
            'processing': '#9932CC',
            'completed': '#00FF00',
            'cancelled': '#FF4444',
            'refunded': '#888888',
            'failed': '#FF0000',
        }
        color = colors.get(obj.status, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def payment_status(self, obj):
        if obj.mercadopago_payment_id:
            return format_html(
                '<span style="color: #00FF00;">✓ Pagado</span><br>'
                '<small>ID: {}</small>',
                obj.mercadopago_payment_id[:20] + '...' if len(obj.mercadopago_payment_id) > 20 else obj.mercadopago_payment_id
            )
        return format_html('<span style="color: #FFA500;">Pendiente</span>')
    payment_status.short_description = 'Pago'
    
    def total_formatted(self, obj):
        return f"${obj.total:,.0f} {obj.currency}"
    total_formatted.short_description = 'Total'
    
    def iva_display(self, obj):
        if obj.iva_amount > 0:
            return f"${obj.iva_amount:,.0f}"
        return '-'
    iva_display.short_description = 'IVA (19%)'
    
    def seller_earnings_display(self, obj):
        return f"${obj.seller_total:,.0f}"
    seller_earnings_display.short_description = 'Pago Vendedor'
    
    def export_to_pdf(self, request, queryset):
        from django.http import HttpResponse
        from .pdf_generator import generate_order_pdf
        
        if queryset.count() == 1:
            order = queryset.first()
            pdf_content = generate_order_pdf(order, order.buyer)
            
            response = HttpResponse(pdf_content, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{order.order_number}.pdf"'
            return response
        else:
            self.message_user(request, 'Selecciona una sola orden para exportar PDF', level='warning')
    export_to_pdf.short_description = 'Exportar PDF'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} órdenes marcadas como completadas.')
    mark_as_completed.short_description = 'Marcar como completadas'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled', cancelled_at=timezone.now())
        self.message_user(request, f'{updated} órdenes canceladas.')
    mark_as_cancelled.short_description = 'Cancelar órdenes'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'order_link', 'product_name', 'seller', 'license_type',
        'quantity', 'unit_price', 'subtotal', 'seller_earnings', 'is_delivered'
    )
    list_filter = ('license_type', 'is_delivered', 'created_at')
    search_fields = ('order__order_number', 'product_name', 'seller__email')
    readonly_fields = ('id', 'created_at', 'iva_amount', 'mercadopago_fee', 'platform_maintenance', 'seller_earnings')
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Orden'
    
    def seller_earnings(self, obj):
        return f"${obj.seller_earnings:,.0f}"
    seller_earnings.short_description = 'Ganancia Vendedor'


@admin.register(ProductDownload)
class ProductDownloadAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'download_count', 'remaining', 'expires_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'product__name')
    readonly_fields = ('id', 'download_token', 'created_at', 'last_downloaded_at')
    
    def remaining(self, obj):
        return obj.remaining_downloads
    remaining.short_description = 'Restantes'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'coupon_type', 'discount_display', 'is_active', 'validity', 'usage')
    list_filter = ('coupon_type', 'is_active', 'status')
    search_fields = ('code',)
    readonly_fields = ('current_uses', 'created_at')
    
    def discount_display(self, obj):
        if obj.coupon_type == 'percentage':
            return f"{obj.discount_value}%"
        return f"${obj.discount_value}"
    discount_display.short_description = 'Descuento'
    
    def validity(self, obj):
        now = timezone.now()
        if obj.valid_until < now:
            return format_html('<span style="color: red;">Expirado</span>')
        if obj.valid_from > now:
            return format_html('<span style="color: orange;">Próximamente</span>')
        return format_html('<span style="color: green;">Válido</span>')
    validity.short_description = 'Validez'
    
    def usage(self, obj):
        if obj.max_uses:
            return f"{obj.current_uses} / {obj.max_uses}"
        return f"{obj.current_uses} / ∞"
    usage.short_description = 'Usos'


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order_link', 'user', 'status_badge', 'refund_amount', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order__order_number', 'user__email', 'reason')
    readonly_fields = ('id', 'created_at', 'processed_at')
    actions = ['approve_refunds', 'reject_refunds']
    
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.id])
        return format_html('<a href="{}">{}</a>', url, obj.order.order_number)
    order_link.short_description = 'Orden'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#FFA500',
            'approved': '#00BFFF',
            'rejected': '#FF4444',
            'processed': '#00FF00',
        }
        color = colors.get(obj.status, '#888888')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Estado'
    
    def approve_refunds(self, request, queryset):
        updated = queryset.update(status='approved', processed_at=timezone.now())
        self.message_user(request, f'{updated} reembolsos aprobados.')
    approve_refunds.short_description = 'Aprobar reembolsos seleccionados'
    
    def reject_refunds(self, request, queryset):
        updated = queryset.update(status='rejected', processed_at=timezone.now())
        self.message_user(request, f'{updated} reembolsos rechazados.')
    reject_refunds.short_description = 'Rechazar reembolsos seleccionados'
