"""
Serializers de Órdenes
"""

from rest_framework import serializers
from django.db import transaction

from .models import Cart, CartItem, Order, OrderItem, ProductDownload, Coupon, Refund


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer de item del carrito."""
    
    product_id = serializers.UUIDField(source='product.id', read_only=True)
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_slug = serializers.CharField(source='product.slug', read_only=True)
    product_image = serializers.SerializerMethodField()
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product_id', 'product_name', 'product_slug',
            'product_image', 'license_type', 'quantity',
            'price_at_add', 'subtotal'
        ]
    
    def get_product_image(self, obj):
        if obj.product.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product.thumbnail.url)
            return obj.product.thumbnail.url
        return None


class CartSerializer(serializers.ModelSerializer):
    """Serializer del carrito."""
    
    items = CartItemSerializer(many=True, read_only=True)
    items_count = serializers.IntegerField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    platform_fee = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    seller_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 'items', 'items_count', 'subtotal',
            'platform_fee', 'seller_total', 'currency',
            'created_at', 'updated_at'
        ]


class CartAddItemSerializer(serializers.Serializer):
    """Serializer para agregar item al carrito."""
    
    product_id = serializers.UUIDField()
    license_type = serializers.ChoiceField(
        choices=[('regular', 'Regular'), ('extended', 'Extended')],
        default='regular'
    )
    quantity = serializers.IntegerField(min_value=1, default=1)
    
    def validate_product_id(self, value):
        from products.models import Product
        
        try:
            product = Product.objects.get(id=value, status=Product.Status.APPROVED)
        except Product.DoesNotExist:
            raise serializers.ValidationError('Producto no encontrado o no disponible.')
        
        return value
    
    def create(self, validated_data):
        product_id = validated_data['product_id']
        license_type = validated_data['license_type']
        user = self.context['request'].user
        
        from products.models import Product
        product = Product.objects.get(id=product_id)
        
        if license_type == 'extended':
            if not product.has_extended_license:
                raise serializers.ValidationError({
                    'license_type': 'Este producto no tiene licencia extendida.'
                })
            price = product.extended_license_price or product.price
        else:
            price = product.regular_license_price or product.price
        
        if user.is_authenticated:
            cart, _ = Cart.objects.get_or_create(user=user)
        else:
            session_key = self.context['request'].session.session_key
            if not session_key:
                self.context['request'].session.create()
            cart, _ = Cart.objects.get_or_create(session_key=self.context['request'].session.session_key)
        
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={
                'license_type': license_type,
                'price_at_add': price,
                'quantity': validated_data['quantity']
            }
        )
        
        if not created:
            cart_item.quantity += validated_data['quantity']
            cart_item.save()
        
        return cart


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer de item de orden."""
    
    product_image = serializers.SerializerMethodField()
    can_download = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    download_count = serializers.IntegerField(read_only=True)
    max_downloads = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product_name', 'product_slug', 'product_image',
            'seller_name', 'license_type', 'unit_price',
            'quantity', 'subtotal', 'discount',
            'can_download', 'download_url', 'download_count', 'max_downloads'
        ]
    
    def get_product_image(self, obj):
        if obj.product_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.product_image)
            return obj.product_image
        return None
    
    def get_can_download(self, obj):
        return obj.can_download
    
    def get_download_url(self, obj):
        if obj.can_download:
            request = self.context.get('request')
            return f"/api/v1/orders/downloads/{obj.id}/"
        return None


class OrderSerializer(serializers.ModelSerializer):
    """Serializer de orden."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    buyer_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'buyer_name', 'status',
            'payment_method', 'email', 'phone',
            'subtotal', 'discount', 'tax', 'total', 'currency',
            'coupon_code', 'coupon_discount',
            'notes', 'created_at', 'paid_at', 'completed_at'
        ]
    
    def get_buyer_name(self, obj):
        return obj.buyer.get_display_name()


class OrderDetailSerializer(OrderSerializer):
    """Serializer detalle de orden."""
    
    items = OrderItemSerializer(many=True, read_only=True)
    billing_address = serializers.SerializerMethodField()
    
    class Meta(OrderSerializer.Meta):
        fields = OrderSerializer.Meta.fields + [
            'billing_address', 'mercadopago_payment_id', 'mercadopago_merchant_order_id',
            'admin_notes', 'ip_address'
        ]
    
    def get_billing_address(self, obj):
        if obj.billing_address:
            return {
                'street': obj.billing_address.street,
                'city': obj.billing_address.city,
                'state': obj.billing_address.state,
                'postal_code': obj.billing_address.postal_code,
                'country': obj.billing_address.country,
                'full_address': obj.billing_address.full_address,
            }
        return None


class CheckoutSerializer(serializers.Serializer):
    """Serializer para proceso de checkout."""
    
    email = serializers.EmailField(required=True)
    phone = serializers.CharField(max_length=20, required=False)
    coupon_code = serializers.CharField(max_length=50, required=False)
    notes = serializers.CharField(required=False, allow_blank=True)
    billing_address_id = serializers.UUIDField(required=False)
    
    def validate_coupon_code(self, value):
        if value:
            try:
                coupon = Coupon.objects.get(code=value)
                user = self.context['request'].user
                cart = self.context.get('cart')
                
                is_valid, message = coupon.is_valid(user, float(cart.subtotal) if cart else 0)
                if not is_valid:
                    raise serializers.ValidationError(message)
                
            except Coupon.DoesNotExist:
                raise serializers.ValidationError('Cupón no válido.')
        
        return value
    
    def validate_billing_address_id(self, value):
        if value:
            user = self.context['request'].user
            from users.models import UserAddress
            try:
                address = UserAddress.objects.get(id=value, user=user)
            except UserAddress.DoesNotExist:
                raise serializers.ValidationError('Dirección no encontrada.')
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        user = self.context['request'].user
        cart = self.context.get('cart')
        
        coupon_code = validated_data.pop('coupon_code', None)
        billing_address_id = validated_data.pop('billing_address_id', None)
        notes = validated_data.pop('notes', '')
        
        coupon = None
        if coupon_code:
            coupon = Coupon.objects.get(code=coupon_code)
        
        billing_address = None
        if billing_address_id:
            from users.models import UserAddress
            billing_address = UserAddress.objects.get(id=billing_address_id)
        
        order = Order.objects.create(
            buyer=user,
            email=validated_data.get('email', user.email),
            phone=validated_data.get('phone', ''),
            subtotal=cart.subtotal,
            total=cart.total,
            coupon=coupon,
            coupon_code=coupon_code or '',
            coupon_discount=cart.discount if coupon else 0,
            billing_address=billing_address,
            notes=notes,
            ip_address=self.context['request'].META.get('REMOTE_ADDR'),
            user_agent=self.context['request'].META.get('HTTP_USER_AGENT', '')[:500],
        )
        
        if coupon:
            coupon.current_uses += 1
            coupon.save()
        
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                product_name=cart_item.product.name,
                product_slug=cart_item.product.slug,
                seller=cart_item.product.seller,
                seller_name=cart_item.product.seller.get_display_name(),
                license_type=cart_item.license_type,
                unit_price=cart_item.price_at_add,
                quantity=cart_item.quantity,
                subtotal=cart_item.subtotal,
            )
        
        cart.items.all().delete()
        
        return order


class DownloadSerializer(serializers.ModelSerializer):
    """Serializer para descarga."""
    
    download_url = serializers.SerializerMethodField()
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductDownload
        fields = [
            'id', 'product_name', 'download_token', 'download_url',
            'download_count', 'max_downloads', 'remaining_downloads',
            'expires_at', 'last_downloaded_at', 'is_active'
        ]
    
    def get_download_url(self, obj):
        return f"/api/v1/orders/downloads/{obj.id}/token/{obj.download_token}/"


class CouponSerializer(serializers.ModelSerializer):
    """Serializer de cupón."""
    
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'coupon_type', 'discount_value',
            'min_purchase_amount', 'max_discount_amount',
            'valid_from', 'valid_until', 'is_active'
        ]


class RefundSerializer(serializers.ModelSerializer):
    """Serializer de reembolso."""
    
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    product_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Refund
        fields = [
            'id', 'order', 'order_number', 'order_item', 'product_name',
            'reason', 'status', 'refund_amount',
            'admin_notes', 'created_at', 'processed_at'
        ]
    
    def get_product_name(self, obj):
        if obj.order_item:
            return obj.order_item.product_name
        return None


class RefundCreateSerializer(serializers.Serializer):
    """Serializer para crear reembolso."""
    
    order_id = serializers.UUIDField()
    order_item_id = serializers.UUIDField(required=False)
    reason = serializers.CharField(max_length=1000)
    
    def validate_order_id(self, value):
        user = self.context['request'].user
        try:
            order = Order.objects.get(id=value, buyer=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError('Orden no encontrada.')
        
        if order.status != Order.Status.COMPLETED:
            raise serializers.ValidationError('Solo puedes solicitar reembolso de órdenes completadas.')
        
        return value
    
    def create(self, validated_data):
        user = self.context['request'].user
        order = Order.objects.get(id=validated_data['order_id'])
        
        refund_amount = order.total
        
        order_item = None
        if 'order_item_id' in validated_data:
            order_item = order.items.filter(id=validated_data['order_item_id']).first()
            if order_item:
                refund_amount = order_item.subtotal
        
        refund = Refund.objects.create(
            order=order,
            order_item=order_item,
            user=user,
            reason=validated_data['reason'],
            refund_amount=refund_amount,
        )
        
        return refund
