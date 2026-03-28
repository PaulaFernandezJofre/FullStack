"""
Vistas de Órdenes
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, redirect
from django.http import FileResponse, HttpResponse
from django.conf import settings
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from django.contrib.admin.views.decorators import staff_member_required

from .models import Cart, CartItem, Order, OrderItem, ProductDownload, Coupon
from .serializers import (
    CartSerializer, CartAddItemSerializer, OrderSerializer, OrderDetailSerializer, CheckoutSerializer,
    DownloadSerializer, CouponSerializer, RefundSerializer, RefundCreateSerializer
)


class CheckoutTemplateView(View):
    """Vista de checkout para renderizar template."""
    
    template_name = 'orders/checkout.html'
    
    def get(self, request):
        if not request.user.is_authenticated:
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


class CartTemplateView(View):
    """Vista del carrito de compras."""
    
    template_name = 'orders/cart.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=request.user)
        else:
            cart = None
        
        if not cart:
            cart_items = []
            subtotal = 0
            discount = 0
            total = 0
        else:
            cart_items = cart.items.select_related('product', 'product__seller').all()
            subtotal = cart.subtotal
            discount = 0
            total = subtotal - discount
        
        context = {
            'cart_items': cart_items,
            'subtotal': subtotal,
            'discount': discount,
            'total': total,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        """Agregar producto al carrito."""
        from .serializers import CartAddItemSerializer
        
        if not request.user.is_authenticated:
            return redirect('account:login')
        
        serializer = CartAddItemSerializer(
            data=request.POST,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return redirect('orders:cart')
        
        return redirect('products:product-list')


class CartRemoveItemView(View):
    """Quitar item del carrito."""
    
    @method_decorator(csrf_protect)
    def post(self, request, item_id):
        if not request.user.is_authenticated:
            return redirect('account:login')
        
        try:
            cart = Cart.objects.get(user=request.user)
            item = cart.items.get(id=item_id)
            item.delete()
        except (Cart.DoesNotExist, CartItem.DoesNotExist):
            pass
        
        return redirect('orders:cart')


class ApplyCouponView(View):
    """Aplicar cupón de descuento."""
    
    @method_decorator(csrf_protect)
    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('account:login')
        
        code = request.POST.get('code', '').strip()
        if code:
            try:
                coupon = Coupon.objects.get(code=code, is_active=True)
                cart = Cart.objects.get(user=request.user)
                
                is_valid, message = coupon.is_valid(
                    request.user,
                    float(cart.subtotal) if cart.subtotal else 0
                )
                
                if is_valid:
                    cart.coupon = coupon
                    cart.save()
                else:
                    request.session['coupon_error'] = message
            except Coupon.DoesNotExist:
                request.session['coupon_error'] = 'Cupón no válido'
        
        return redirect('orders:cart')


class CheckoutProcessView(View):
    """Procesa el checkout y redirige a Mercado Pago."""
    
    template_name = 'orders/checkout.html'
    
    @method_decorator(csrf_protect)
    def post(self, request):
        if not request.user.is_authenticated:
            login_url = redirect('account:login')
            login_url['Location'] += '?next=' + request.path
            return login_url
        
        cart = Cart.objects.filter(user=request.user).first()
        if not cart or cart.items.count() == 0:
            messages.error(request, 'Tu carrito está vacío')
            return redirect('orders:cart')
        
        email = request.POST.get('email', request.user.email)
        
        order = Order.objects.create(
            buyer=request.user,
            email=email,
            phone=request.POST.get('phone', ''),
            payment_method='mercadopago',
            status=Order.Status.PENDING,
            ip_address=self._get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
        )
        
        for cart_item in cart.items.select_related('product', 'product__seller').all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_slug=cart_item.product.slug,
                product_image=cart_item.product.thumbnail.url if cart_item.product.thumbnail else '',
                seller=cart_item.product.seller,
                seller_name=cart_item.product.seller.get_display_name(),
                license_type=cart_item.license_type,
                unit_price=cart_item.price_at_add,
                quantity=cart_item.quantity,
                subtotal=cart_item.subtotal,
            )
        
        mp_service = None
        try:
            from payments.mercadopago_service import MercadoPagoService
            
            items = []
            for item in order.items.select_related('product').all():
                items.append({
                    "id": str(item.id)[:50],
                    "title": item.product.name[:100],
                    "quantity": item.quantity,
                    "currency_id": order.currency,
                    "unit_price": float(item.unit_price)
                })
            
            payer = {
                "name": request.user.first_name or '',
                "surname": request.user.last_name or '',
                "email": email,
            }
            
            site_url = settings.SITE_URL.rstrip('/')
            if not site_url.startswith(('http://', 'https://')):
                site_url = 'https://' + site_url
            
            back_urls = {
                "success": f"{site_url}/orders/mercadopago/success/{order.id}/",
                "pending": f"{site_url}/orders/mercadopago/success/{order.id}/",
                "failure": f"{site_url}/orders/checkout/",
            }
            
            mp_service = MercadoPagoService()
            result = mp_service.create_preference(
                items=items,
                payer=payer,
                order=order,
                back_urls=back_urls
            )
            
            if result.get('success'):
                init_point = result.get('sandbox_init_point') if mp_service.environment == 'sandbox' \
                    else result.get('init_point')
                
                cart.items.all().delete()
                
                return redirect(init_point)
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating Mercado Pago preference: {e}")
        
        messages.error(request, 'Error al procesar el pago. Intenta de nuevo.')
        return redirect('orders:checkout')
    
    @staticmethod
    def _get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')


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


@staff_member_required
def download_order_pdf(request, order_id):
    """Descarga el PDF del receipt de una orden."""
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return HttpResponse('Orden no encontrada', status=404)
    
    from .pdf_generator import generate_order_pdf
    
    buyer = order.buyer
    pdf_content = generate_order_pdf(order, buyer)
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{order.order_number}.pdf"'
    
    return response


def view_order_pdf(request, order_id):
    """Vista el PDF del receipt de una orden (sin descarga automática)."""
    try:
        order = Order.objects.get(id=order_id)
        if order.buyer != request.user and not request.user.is_staff:
            return HttpResponse('No tienes permiso', status=403)
    except Order.DoesNotExist:
        return HttpResponse('Orden no encontrada', status=404)
    
    from .pdf_generator import generate_order_pdf
    
    buyer = order.buyer
    pdf_content = generate_order_pdf(order, buyer)
    
    response = HttpResponse(pdf_content, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="receipt_{order.order_number}.pdf"'
    
    return response


class SellerReportPDFView(View):
    """Genera reporte PDF de ventas para vendedores."""
    
    def get(self, request):
        if not request.user.is_authenticated:
            return HttpResponse('No autenticado', status=401)
        
        if not hasattr(request.user, 'is_seller') or not request.user.is_seller:
            return HttpResponse('No eres vendedor', status=403)
        
        from django.utils import timezone
        from datetime import timedelta
        from .pdf_generator import generate_seller_pdf
        
        days = int(request.GET.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        orders = Order.objects.filter(
            items__seller=request.user,
            status__in=['completed', 'paid'],
            created_at__gte=start_date,
            created_at__lte=end_date
        ).distinct()
        
        pdf_content = generate_seller_pdf(
            request.user,
            start_date=start_date,
            end_date=end_date,
            orders=orders
        )
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="reporte_ventas_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf"'
        
        return response
