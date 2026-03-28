"""
Vistas de Pagos
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Payout, Transaction, SellerEarning
from .serializers import (
    PayoutSerializer, TransactionSerializer,
    SellerEarningSerializer, PayoutRequestSerializer
)


class PayoutViewSet(viewsets.ModelViewSet):
    """Gestión de pagos a vendedores."""
    
    serializer_class = PayoutSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Payout.objects.filter(seller=self.request.user)
    
    @action(detail=False, methods=['post'])
    def request(self, request):
        """Solicitar pago."""
        serializer = PayoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        amount = serializer.validated_data['amount']
        method = serializer.validated_data['method']
        
        stats = request.user.seller_stats
        if stats.available_earnings < amount:
            return Response(
                {'error': 'No tienes suficientes ganancias disponibles'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payout = Payout.objects.create(
            seller=request.user,
            amount=amount,
            method=method,
            bank_name=request.user.bank_name,
            bank_account_last4=request.user.bank_account_number[-4:] if request.user.bank_account_number else '',
        )
        
        stats.pending_payouts += amount
        stats.available_earnings -= amount
        stats.save()
        
        return Response(
            PayoutSerializer(payout).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Resumen de ganancias."""
        stats = request.user.seller_stats
        
        return Response({
            'total_earnings': float(stats.total_earnings),
            'available_earnings': float(stats.available_earnings),
            'pending_payouts': float(stats.pending_payouts),
            'total_paid_out': float(stats.total_paid_out),
            'total_sales': stats.total_sales,
        })


class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """Transacciones del usuario."""
    
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)


class EarningsViewSet(viewsets.ReadOnlyModelViewSet):
    """Ganancias del vendedor."""
    
    serializer_class = SellerEarningSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return SellerEarning.objects.filter(seller=self.request.user)
