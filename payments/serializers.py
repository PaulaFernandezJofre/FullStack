"""
Serializers de Pagos
"""

from rest_framework import serializers
from .models import Payout, Transaction, SellerEarning, PlatformRevenue


class PayoutSerializer(serializers.ModelSerializer):
    """Serializer de pago a vendedor."""
    
    seller_email = serializers.EmailField(source='seller.email', read_only=True)
    seller_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Payout
        fields = [
            'id', 'payout_number', 'seller', 'seller_email', 'seller_name',
            'amount', 'currency', 'method', 'bank_name', 'bank_account_last4',
            'status', 'notes', 'requested_at', 'processed_at', 'completed_at'
        ]
    
    def get_seller_name(self, obj):
        return obj.seller.get_display_name()


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer de transacción."""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_number', 'user', 'user_email',
            'transaction_type', 'amount', 'currency',
            'order', 'description', 'status',
            'created_at', 'completed_at'
        ]


class SellerEarningSerializer(serializers.ModelSerializer):
    """Serializer de ganancias de vendedor."""
    
    seller_name = serializers.SerializerMethodField()
    
    class Meta:
        model = SellerEarning
        fields = [
            'id', 'seller', 'seller_name', 'source',
            'order', 'order_item', 'gross_amount', 'commission_rate',
            'commission_amount', 'net_amount', 'currency',
            'is_available', 'payout', 'payout_at', 'created_at'
        ]
    
    def get_seller_name(self, obj):
        return obj.seller.get_display_name()


class PayoutRequestSerializer(serializers.Serializer):
    """Serializer para solicitar pago."""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    method = serializers.ChoiceField(choices=['mercadopago', 'bank_transfer', 'paypal'])
    
    def validate_amount(self, value):
        from django.conf import settings
        min_amount = settings.MIN_WITHDRAWAL_AMOUNT
        if value < min_amount:
            raise serializers.ValidationError(
                f'El monto mínimo para retiro es ${min_amount}'
            )
        return value
