"""
Admin de Pedidos y Carritos
"""

from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, ProductDownload, Coupon, Refund


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'buyer', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('order_number',)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'license_type')


@admin.register(ProductDownload)
class ProductDownloadAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'download_count')


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_value', 'coupon_type', 'is_active')


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'reason')
