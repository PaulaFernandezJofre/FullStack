"""
Admin de Finanzas
Dashboard financiero completo con distribución de pagos
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Avg
from django.urls import path
from django.shortcuts import render
from django.db.models.functions import TruncDay, TruncMonth
from django.utils import timezone

from .models import (
    Account, PaymentDistribution, FinancialTransaction,
    PayoutRequest, CategoryFinancialSummary
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_type', 'percentage', 'balance_display', 'is_active']
    list_filter = ['account_type', 'is_active']
    readonly_fields = ['total_credits', 'total_debits', 'created_at', 'updated_at']
    
    def balance_display(self, obj):
        return format_html(
            '<strong style="color: #3ddc84;">${:,.2f}</strong>',
            obj.balance
        )
    balance_display.short_description = 'Balance'


@admin.register(PaymentDistribution)
class PaymentDistributionAdmin(admin.ModelAdmin):
    list_display = ['distribution_number', 'gross_amount', 'iva_display', 'mp_fee_display', 
                    'platform_fee_display', 'seller_amount_display', 'category', 'status', 'created_at']
    list_filter = ['status', 'category', 'created_at']
    search_fields = ['distribution_number', 'order__order_number']
    readonly_fields = ['distribution_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def iva_display(self, obj):
        return format_html('<span style="color: #4a9eff;">${:,.2f}</span>', obj.iva_amount)
    iva_display.short_description = 'IVA (19%)'
    
    def mp_fee_display(self, obj):
        return format_html('<span style="color: #ffc107;">${:,.2f}</span>', obj.mercadopago_fee)
    mp_fee_display.short_description = 'MP Fee'
    
    def platform_fee_display(self, obj):
        return format_html('<span style="color: #6f42c1;">${:,.2f}</span>', obj.platform_fee)
    platform_fee_display.short_description = 'Platform'
    
    def seller_amount_display(self, obj):
        return format_html('<strong style="color: #3ddc84;">${:,.2f}</strong>', obj.seller_amount)
    seller_amount_display.short_description = 'Vendedor'


@admin.register(FinancialTransaction)
class FinancialTransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_number', 'transaction_type', 'account', 'amount', 'user', 'status', 'created_at']
    list_filter = ['transaction_type', 'account', 'status', 'created_at']
    search_fields = ['transaction_number', 'user__email']
    readonly_fields = ['transaction_number', 'created_at', 'completed_at']
    date_hierarchy = 'created_at'


@admin.register(PayoutRequest)
class PayoutRequestAdmin(admin.ModelAdmin):
    list_display = ['payout_number', 'seller', 'gross_amount', 'net_amount', 'payout_method', 'status', 'requested_at']
    list_filter = ['status', 'payout_method', 'requested_at']
    search_fields = ['payout_number', 'seller__email']
    readonly_fields = ['payout_number', 'requested_at', 'completed_at']
    date_hierarchy = 'requested_at'
    
    actions = ['process_payouts', 'complete_payouts']
    
    @admin.action(description='Procesar pagos seleccionados')
    def process_payouts(self, request, queryset):
        for payout in queryset.filter(status='pending'):
            payout.status = 'processing'
            payout.processed_at = timezone.now()
            payout.save()
    
    @admin.action(description='Completar pagos seleccionados')
    def complete_payouts(self, request, queryset):
        for payout in queryset.filter(status='processing'):
            payout.status = 'completed'
            payout.completed_at = timezone.now()
            payout.save()


@admin.register(CategoryFinancialSummary)
class CategoryFinancialSummaryAdmin(admin.ModelAdmin):
    list_display = ['category', 'total_sales', 'total_revenue_display', 
                    'iva_total', 'mp_total', 'platform_total', 'seller_total_display']
    readonly_fields = ['total_sales', 'total_revenue', 'total_iva', 'total_mercadopago_fees',
                      'total_platform_fees', 'total_seller_payouts', 'updated_at']
    
    def total_revenue_display(self, obj):
        return format_html('<strong>${:,.2f}</strong>', obj.total_revenue)
    total_revenue_display.short_description = 'Ingresos'
    
    def seller_total_display(self, obj):
        return format_html('<span style="color: #3ddc84;">${:,.2f}</span>', obj.total_seller_payouts)
    seller_total_display.short_description = 'Vendedores'
    
    def iva_total(self, obj):
        return format_html('<span style="color: #4a9eff;">${:,.2f}</span>', obj.total_iva)
    iva_total.short_description = 'IVA'
    
    def mp_total(self, obj):
        return format_html('<span style="color: #ffc107;">${:,.2f}</span>', obj.total_mercadopago_fees)
    mp_total.short_description = 'MP Fee'
    
    def platform_total(self, obj):
        return format_html('<span style="color: #6f42c1;">${:,.2f}</span>', obj.total_platform_fees)
    platform_total.short_description = 'Platform'
