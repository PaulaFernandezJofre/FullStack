"""
Admin de Pagos
"""

from django.contrib import admin
from .models import Payout, PayoutOrder, Transaction, SellerEarning, PlatformRevenue, PaymentMethod


@admin.register(Payout)
class PayoutAdmin(admin.ModelAdmin):
    list_display = ('payout_number', 'seller', 'amount', 'method', 'status')


@admin.register(PayoutOrder)
class PayoutOrderAdmin(admin.ModelAdmin):
    list_display = ('payout', 'order')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'amount')


@admin.register(SellerEarning)
class SellerEarningAdmin(admin.ModelAdmin):
    list_display = ('seller', 'order_item', 'gross_amount')


@admin.register(PlatformRevenue)
class PlatformRevenueAdmin(admin.ModelAdmin):
    list_display = ('source', 'gross_amount', 'net_amount')


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'type', 'is_default')
