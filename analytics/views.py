"""
Vistas de Analítica
"""

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta

from .models import DailyStats
from .serializers import DailyStatsSerializer


class IsAdminUser(permissions.BasePermission):
    """Solo permite acceso a administradores."""
    
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class AnalyticsViewSet(viewsets.ReadOnlyModelViewSet):
    """API de analítica para el dashboard."""
    
    serializer_class = DailyStatsSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        return DailyStats.objects.all()
    
    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Datos del dashboard principal."""
        today = timezone.now().date()
        thirty_days_ago = today - timedelta(days=30)
        sixty_days_ago = today - timedelta(days=60)
        
        current_period = DailyStats.objects.filter(date__gte=thirty_days_ago)
        previous_period = DailyStats.objects.filter(date__gte=sixty_days_ago, date__lt=thirty_days_ago)
        
        current_revenue = current_period.aggregate(total=Sum('total_revenue'))['total'] or 0
        current_orders = current_period.aggregate(total=Sum('total_orders'))['total'] or 0
        
        previous_revenue = previous_period.aggregate(total=Sum('total_revenue'))['total'] or 0
        previous_orders = previous_period.aggregate(total=Sum('total_orders'))['total'] or 0
        
        revenue_change = 0
        if previous_revenue > 0:
            revenue_change = ((current_revenue - previous_revenue) / previous_revenue) * 100
        
        orders_change = 0
        if previous_orders > 0:
            orders_change = ((current_orders - previous_orders) / previous_orders) * 100
        
        from users.models import User
        from products.models import Product
        from support.models import SupportTicket
        
        return Response({
            'total_revenue': float(current_revenue),
            'total_orders': current_orders,
            'total_users': User.objects.count(),
            'total_products': Product.objects.filter(status=Product.Status.APPROVED).count(),
            'pending_tickets': SupportTicket.objects.filter(status__in=['open', 'in_progress']).count(),
            'revenue_change': round(revenue_change, 2),
            'orders_change': round(orders_change, 2),
            'period': 'last_30_days',
        })
    
    @action(detail=False, methods=['get'])
    def revenue_chart(self, request):
        """Datos para gráfico de ingresos."""
        days = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        start_date = today - timedelta(days=days)
        
        stats = DailyStats.objects.filter(
            date__gte=start_date
        ).order_by('date')
        
        data = []
        for stat in stats:
            data.append({
                'date': stat.date.isoformat(),
                'revenue': float(stat.total_revenue),
                'platform_revenue': float(stat.total_platform_revenue),
                'seller_payouts': float(stat.total_seller_payouts),
            })
        
        return Response(data)
    
    @action(detail=False, methods=['get'])
    def sales_by_category(self, request):
        """Ventas por categoría."""
        from products.models import Product
        from orders.models import OrderItem
        
        categories = Product.objects.filter(
            status=Product.Status.APPROVED
        ).values('category__name').annotate(
            total_sales=Sum('order_items__subtotal'),
            count=Count('id')
        ).order_by('-total_sales')[:10]
        
        return Response(list(categories))
    
    @action(detail=False, methods=['get'])
    def top_products(self, request):
        """Productos más vendidos."""
        from products.models import Product
        from products.serializers import ProductListSerializer
        
        products = Product.objects.filter(
            status=Product.Status.APPROVED
        ).order_by('-sales')[:10]
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
