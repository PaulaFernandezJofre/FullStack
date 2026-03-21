"""
Serializers de Analítica
"""

from rest_framework import serializers
from .models import DailyStats, ProductStats, CategoryStats


class DailyStatsSerializer(serializers.ModelSerializer):
    """Serializer de estadísticas diarias."""
    
    class Meta:
        model = DailyStats
        fields = [
            'date', 'total_orders', 'completed_orders', 'cancelled_orders',
            'total_revenue', 'total_platform_revenue', 'total_seller_payouts',
            'new_products', 'total_product_views', 'total_product_sales',
            'new_users', 'new_sellers', 'new_buyers',
            'new_support_tickets', 'resolved_tickets',
            'total_page_views', 'unique_visitors'
        ]


class DashboardSerializer(serializers.Serializer):
    """Serializer para dashboard principal."""
    
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_orders = serializers.IntegerField()
    total_users = serializers.IntegerField()
    total_products = serializers.IntegerField()
    pending_tickets = serializers.IntegerField()
    revenue_change = serializers.FloatField()
    orders_change = serializers.FloatField()
