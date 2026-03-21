"""
Vistas de Órdenes
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from django.http import FileResponse
from django.conf import settings
from django.views import View

from .models import Cart, CartItem, Order, OrderItem, ProductDownload, Coupon, Refund
from .serializers import (
    CartSerializer, CartItemSerializer, CartAddItemSerializer, OrderSerializer, OrderDetailSerializer, CheckoutSerializer,
    DownloadSerializer, CouponSerializer, RefundSerializer, RefundCreateSerializer
)


class CheckoutTemplateView(View):
    """Vista de checkout para renderizar template."""
    
    template_name = 'orders/checkout.html'
    
    def get(self, request):
        if not request.user.is_authenticated:
            from django.shortcuts import redirect
            login_url = redirect('account:login')
            login_url['Location'] += '?next=' + request.path
            return login_url
        
        cart, _ = Cart.objects.get_or_create(user=request.user)
        cart_items = cart.items.select_related('product').all()
        
        subtotal = cart.subtotal
        discount = cart.discount or 0
        iva = 0
        iva_rate = 0
        
        if getattr(settings, 'MERCADO_PAGO_CHILE_IVA', False):
            iva_rate = settings.MERCADO_PAGO_CHILE_IVA_RATE
            iva = float(subtotal) * (iva_rate / 100)
        
        total = float(subtotal) - float(discount) + iva
        
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'discount': discount,
            'iva': round(iva, 2),
            'iva_rate': iva_rate,
            'total': round(total, 2),
            'chile_iva_enabled': getattr(settings, 'MERCADO_PAGO_CHILE_IVA', False),
        }
        return render(request, self.template_name, context)


class CartViewSet(viewsets.ModelViewSet):
    """Carrito de compras."""
    
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)
    
    def get_object(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart
    
    @action(detail=False, methods=['get', 'post'])
    def add(self, request):
        """Agrega item al carrito."""
        serializer = CartAddItemSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        cart = serializer.save()
        
        return Response(CartSerializer(cart, context={'request': request}).data)
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Quita item del carrito."""
        cart = self.get_object()
        item_id = request.data.get('item_id')
        
        try:
            item = cart.items.get(id=item_id)
            item.delete()
            return Response({'status': 'removed'})
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Item no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Vacía el carrito."""
        cart = self.get_object()
        cart.clear()
        return Response({'status': 'cleared'})


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """Órdenes del usuario."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrderDetailSerializer
        return OrderSerializer
    
    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user)
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Procesa el checkout."""
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or cart.items.count() == 0:
            return Response(
                {'error': 'El carrito está vacío'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = CheckoutSerializer(
            data=request.data,
            context={'request': request, 'cart': cart}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        return Response(
            OrderDetailSerializer(order, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def request_refund(self, request, pk=None):
        """Solicita reembolso."""
        order = self.get_object()
        
        serializer = RefundCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        refund = serializer.save()
        
        return Response(
            RefundSerializer(refund).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Lista de descargas disponibles."""
        order = self.get_object()
        downloads = ProductDownload.objects.filter(
            order_item__order=order,
            user=request.user
        )
        
        serializer = DownloadSerializer(
            downloads,
            many=True,
            context={'request': request}
        )
        return Response(serializer.data)


class DownloadViewSet(viewsets.ViewSet):
    """Gestión de descargas."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def retrieve(self, request, pk=None):
        """Genera enlace de descarga."""
        try:
            order_item = OrderItem.objects.get(id=pk, order__buyer=request.user)
        except OrderItem.DoesNotExist:
            return Response(
                {'error': 'Item no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not order_item.can_download:
            return Response(
                {'error': 'No tienes descargas disponibles'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        download = ProductDownload.objects.create(
            order_item=order_item,
            user=request.user,
            product=order_item.product,
            expires_at=order_item.download_expires_at
        )
        
        serializer = DownloadSerializer(download, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='token/(?P<token>[^/.]+)')
    def download_file(self, request, pk=None, token=None):
        """Descarga el archivo."""
        try:
            download = ProductDownload.objects.get(
                id=pk,
                download_token=token,
                user=request.user,
                is_active=True
            )
        except ProductDownload.DoesNotExist:
            return Response(
                {'error': 'Enlace de descarga inválido'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if download.is_expired:
            return Response(
                {'error': 'El enlace ha expirado'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if download.remaining_downloads <= 0:
            return Response(
                {'error': 'Has alcanzado el límite de descargas'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        product = download.product
        if not product.file:
            return Response(
                {'error': 'Archivo no disponible'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        download.record_download(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
        
        return FileResponse(
            product.file,
            as_attachment=True,
            filename=f"{product.slug}.zip"
        )


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """Gestión de cupones."""
    
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'code'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        from django.utils import timezone
        now = timezone.now()
        return queryset.filter(valid_from__lte=now, valid_until__gte=now)
    
    @action(detail=False, methods=['post'])
    def validate(self, request):
        """Valida un cupón."""
        code = request.data.get('code')
        if not code:
            return Response(
                {'valid': False, 'error': 'Código requerido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            coupon = Coupon.objects.get(code=code, is_active=True)
            is_valid, message = coupon.is_valid(request.user, float(request.data.get('subtotal', 0)))
            
            return Response({
                'valid': is_valid,
                'error': message if not is_valid else None,
                'discount_value': float(coupon.discount_value),
                'coupon_type': coupon.coupon_type,
            })
        except Coupon.DoesNotExist:
            return Response({
                'valid': False,
                'error': 'Cupón no válido'
            })
