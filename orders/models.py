"""
Modelos de Órdenes y Carrito de Compras
Sistema completo de gestión de pedidos
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

import uuid


class Cart(models.Model):
    """Carrito de compras."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart',
        null=True,
        blank=True
    )
    session_key = models.CharField(max_length=40, blank=True)
    
    # Moneda
    currency = models.CharField(max_length=3, default='MXN')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'carts'
        verbose_name = _('carrito')
        verbose_name_plural = _('carritos')
    
    def __str__(self):
        return f"Carrito {self.id}"
    
    @property
    def items_count(self):
        return self.items.count()
    
    @property
    def subtotal(self):
        return sum(item.subtotal for item in self.items.all())
    
    @property
    def total(self):
        return self.subtotal
    
    @property
    def platform_fee(self):
        from django.conf import settings
        return self.subtotal * settings.PLATFORM_COMMISSION_RATE
    
    @property
    def seller_total(self):
        return self.subtotal * settings.SELLER_COMMISSION_RATE
    
    def clear(self):
        self.items.all().delete()
    
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class CartItem(models.Model):
    """Items del carrito."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='cart_items'
    )
    
    # Si el producto tiene múltiples licencias
    license_type = models.CharField(
        _('tipo de licencia'),
        max_length=20,
        choices=[
            ('regular', 'Licencia Regular'),
            ('extended', 'Licencia Extendida'),
        ],
        default='regular'
    )
    
    quantity = models.PositiveIntegerField(default=1)
    price_at_add = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'cart_items'
        verbose_name = _('item del carrito')
        verbose_name_plural = _('items del carrito')
        unique_together = ['cart', 'product']
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    @property
    def subtotal(self):
        return self.price_at_add * self.quantity
    
    def get_price_for_license(self):
        if self.license_type == 'extended' and self.product.has_extended_license:
            return self.product.extended_license_price
        return self.product.regular_license_price or self.product.price


class Order(models.Model):
    """
    Orden principal de compra.
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendiente de pago')
        PAID = 'paid', _('Pagado')
        PROCESSING = 'processing', _('Procesando')
        COMPLETED = 'completed', _('Completado')
        CANCELLED = 'cancelled', _('Cancelado')
        REFUNDED = 'refunded', _('Reembolsado')
        FAILED = 'failed', _('Fallido')
    
    class PaymentMethod(models.TextChoices):
        MERCADO_PAGO = 'mercadopago', 'Mercado Pago'
        PAYPAL = 'paypal', 'PayPal'
        TRANSFER = 'transfer', 'Transferencia'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_number = models.CharField(_('número de orden'), max_length=20, unique=True)
    
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_method = models.CharField(
        _('método de pago'),
        max_length=20,
        choices=PaymentMethod.choices,
        blank=True
    )
    
    # Información de contacto
    email = models.EmailField(_('email'))
    phone = models.CharField(_('teléfono'), max_length=20, blank=True)
    
    # Totales
    subtotal = models.DecimalField(
        _('subtotal'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount = models.DecimalField(
        _('descuento'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    total = models.DecimalField(
        _('total'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    currency = models.CharField(max_length=3, default='CLP')
    
    # Distribución Financiera Completa (calculada al momento del pago)
    iva_amount = models.DecimalField(
        _('monto IVA Chile'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    mercadopago_fee = models.DecimalField(
        _('comisión Mercado Pago'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    platform_maintenance = models.DecimalField(
        _('mantención plataforma'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    seller_total = models.DecimalField(
        _('pago neto vendedor'),
        max_digits=12,
        decimal_places=2,
        default=0
    )
    
    # Dirección de facturación
    billing_address = models.ForeignKey(
        'users.UserAddress',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='billing_orders'
    )
    
    # Notas
    notes = models.TextField(_('notas'), blank=True)
    admin_notes = models.TextField(_('notas de administrador'), blank=True)
    
    # Pagos - Mercado Pago
    mercadopago_payment_id = models.CharField(max_length=100, blank=True)
    mercadopago_merchant_order_id = models.CharField(max_length=100, blank=True)
    
    # Descuentos aplicados
    coupon = models.ForeignKey(
        'Coupon',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders'
    )
    coupon_code = models.CharField(max_length=50, blank=True)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    
    # IP y user agent
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = _('orden')
        verbose_name_plural = _('órdenes')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_number']),
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status', 'created_at']),
        ]
    
    def __str__(self):
        return f"Orden {self.order_number}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = self.generate_order_number()
        if self.pk is None or self.items.exists():
            self.calculate_totals()
        super().save(*args, **kwargs)
    
    def generate_order_number(self):
        """Genera un número de orden único."""
        last_order = Order.objects.order_by('created_at').first()
        if last_order:
            last_number = int(last_order.order_number.replace('ORD-', ''))
            new_number = last_number + 1
        else:
            new_number = 1
        return f"ORD-{new_number:08d}"
    
    def calculate_totals(self):
        """
        Calcula los totales de la orden con distribución financiera completa.
        
        Para $100.000 CLP (ejemplo):
        - Subtotal: $100.000
        - Descuento: -$10.000
        - Después de descuento: $90.000
        
        Distribución sobre monto sin IVA:
        - IVA (19%): ~$14.370
        - Mercado Pago (~6%): ~$4.525
        - Mantención Plataforma (15%): $13.500
        - Vendedor (64%): $57.605
        """
        from decimal import Decimal
        from django.conf import settings
        
        items = self.items.all()
        self.subtotal = sum(item.subtotal for item in items)
        
        if self.coupon:
            self.coupon_discount = self.coupon.calculate_discount(self.subtotal)
        
        self.discount = self.coupon_discount
        
        gross_amount = Decimal(str(self.subtotal - self.discount))
        
        iva_rate = Decimal(str(settings.IVA_RATE))
        mp_rate = Decimal(str(settings.MERCADO_PAGO_FEE_RATE))
        platform_rate = Decimal(str(settings.PLATFORM_MAINTENANCE_RATE))
        
        iva = gross_amount * iva_rate / (Decimal('1') + iva_rate)
        amount_without_iva = gross_amount - iva
        
        mp_fee = amount_without_iva * mp_rate
        
        amount_after_costs = amount_without_iva - mp_fee
        
        platform = gross_amount * platform_rate
        
        seller = amount_after_costs - platform
        
        self.iva_amount = iva.quantize(Decimal('1'))
        self.mercadopago_fee = mp_fee.quantize(Decimal('1'))
        self.platform_maintenance = platform.quantize(Decimal('1'))
        self.seller_total = seller.quantize(Decimal('1'))
        
        self.total = gross_amount
    
    def mark_as_paid(self, mercadopago_payment_id=None, mercadopago_merchant_order_id=None):
        """Marca la orden como pagada."""
        self.status = self.Status.PAID
        self.paid_at = timezone.now()
        if mercadopago_payment_id:
            self.mercadopago_payment_id = mercadopago_payment_id
        if mercadopago_merchant_order_id:
            self.mercadopago_merchant_order_id = mercadopago_merchant_order_id
        self.save()
        
        # Generar descargas para el comprador
        for item in self.items.all():
            item.generate_download_link()
    
    def mark_as_completed(self):
        """Marca la orden como completada."""
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()
    
    def cancel(self):
        """Cancela la orden."""
        self.status = self.Status.CANCELLED
        self.cancelled_at = timezone.now()
        self.save()


class OrderItem(models.Model):
    """
    Item individual dentro de una orden.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    
    # Información del producto al momento de la compra
    product_name = models.CharField(_('nombre del producto'), max_length=200)
    product_slug = models.CharField(max_length=200)
    product_image = models.URLField(blank=True)
    
    # Vendedor
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sold_items'
    )
    seller_name = models.CharField(max_length=200)
    
    # Licencia
    license_type = models.CharField(
        _('tipo de licencia'),
        max_length=20,
        default='regular'
    )
    
    # Precio
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    
    # Descuento aplicado a este item
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    # Distribución financiera para este item
    iva_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    mercadopago_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    platform_maintenance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    seller_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Descarga
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(default=5)
    download_expires_at = models.DateTimeField(blank=True, null=True)
    
    # Estados
    is_delivered = models.BooleanField(default=False)
    delivery_confirmed_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'order_items'
        verbose_name = _('item de orden')
        verbose_name_plural = _('items de orden')
    
    def __str__(self):
        return f"{self.product_name} - {self.order.order_number}"
    
    def save(self, *args, **kwargs):
        from decimal import Decimal
        from django.conf import settings
        
        if not self.subtotal:
            self.subtotal = self.unit_price * self.quantity
        
        if self.subtotal > 0:
            gross_amount = Decimal(str(self.subtotal - self.discount))
            
            iva_rate = Decimal(str(settings.IVA_RATE))
            mp_rate = Decimal(str(settings.MERCADO_PAGO_FEE_RATE))
            platform_rate = Decimal(str(settings.PLATFORM_MAINTENANCE_RATE))
            
            iva = gross_amount * iva_rate / (Decimal('1') + iva_rate)
            amount_without_iva = gross_amount - iva
            
            mp_fee = amount_without_iva * mp_rate
            
            amount_after_costs = amount_without_iva - mp_fee
            
            platform = gross_amount * platform_rate
            
            seller = amount_after_costs - platform
            
            self.iva_amount = iva.quantize(Decimal('1'))
            self.mercadopago_fee = mp_fee.quantize(Decimal('1'))
            self.platform_maintenance = platform.quantize(Decimal('1'))
            self.seller_earnings = seller.quantize(Decimal('1'))
        
        if not self.product_name and self.product:
            self.product_name = self.product.name
            self.product_slug = self.product.slug
            if self.product.thumbnail:
                self.product_image = self.product.thumbnail.url
            self.seller = self.product.seller
            self.seller_name = self.product.seller.get_display_name()
        
        super().save(*args, **kwargs)
    
    @property
    def can_download(self):
        if not self.is_delivered:
            return False
        if self.download_expires_at and timezone.now() > self.download_expires_at:
            return False
        return self.download_count < self.max_downloads
    
    def generate_download_link(self):
        """Genera enlace de descarga para este item."""
        download = ProductDownload.objects.create(
            order_item=self,
            user=self.order.buyer,
            product=self.product,
            expires_at=timezone.now() + timezone.timedelta(days=30)
        )
        self.is_delivered = True
        self.delivery_confirmed_at = timezone.now()
        self.download_expires_at = download.expires_at
        self.save()
        return download


class ProductDownload(models.Model):
    """Enlaces de descarga generados para compradores."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    
    download_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    download_count = models.PositiveIntegerField(default=0)
    max_downloads = models.PositiveIntegerField(default=5)
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_downloaded_at = models.DateTimeField(blank=True, null=True)
    
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'product_downloads'
        verbose_name = _('descarga')
        verbose_name_plural = _('descargas')
    
    def __str__(self):
        return f"Download {self.product.name} - {self.user.email}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def remaining_downloads(self):
        return max(0, self.max_downloads - self.download_count)
    
    def record_download(self, ip_address=None, user_agent=None):
        """Registra una descarga."""
        self.download_count += 1
        self.last_downloaded_at = timezone.now()
        if ip_address:
            self.ip_address = ip_address
        if user_agent:
            self.user_agent = user_agent
        self.save()
        
        self.order_item.download_count = self.download_count
        self.order_item.save()


class Coupon(models.Model):
    """Cupones de descuento."""
    
    class CouponType(models.TextChoices):
        PERCENTAGE = 'percentage', _('Porcentaje')
        FIXED = 'fixed', _('Cantidad fija')
        FREE_SHIPPING = 'free_shipping', _('Envío gratis')
    
    class CouponStatus(models.TextChoices):
        ACTIVE = 'active', _('Activo')
        USED = 'used', _('Usado completamente')
        EXPIRED = 'expired', _('Expirado')
        DISABLED = 'disabled', _('Deshabilitado')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(_('código'), max_length=50, unique=True)
    coupon_type = models.CharField(
        _('tipo'),
        max_length=20,
        choices=CouponType.choices,
        default=CouponType.PERCENTAGE
    )
    
    # Valor del descuento
    discount_value = models.DecimalField(_('valor del descuento'), max_digits=10, decimal_places=2)
    min_purchase_amount = models.DecimalField(
        _('compra mínima'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    max_discount_amount = models.DecimalField(
        _('descuento máximo'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Límites
    max_uses = models.PositiveIntegerField(_('usos máximos'), blank=True, null=True)
    max_uses_per_user = models.PositiveIntegerField(_('usos por usuario'), default=1)
    current_uses = models.PositiveIntegerField(default=0)
    
    # Productos/categorías aplicables
    applicable_products = models.ManyToManyField(
        'products.Product',
        blank=True,
        related_name='applicable_coupons'
    )
    applicable_categories = models.ManyToManyField(
        'products.Category',
        blank=True,
        related_name='applicable_coupons'
    )
    
    # Válidez
    valid_from = models.DateTimeField(_('válido desde'))
    valid_until = models.DateTimeField(_('válido hasta'))
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=CouponStatus.choices,
        default=CouponStatus.ACTIVE
    )
    
    # Restricciones
    is_first_purchase_only = models.BooleanField(_('solo primera compra'), default=False)
    is_active = models.BooleanField(default=True)
    
    # Para vendedores específicos
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='created_coupons'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'coupons'
        verbose_name = _('cupón')
        verbose_name_plural = _('cupones')
    
    def __str__(self):
        return f"{self.code} - {self.discount_value}"
    
    def is_valid(self, user=None, cart_total=0):
        """Verifica si el cupón es válido."""
        now = timezone.now()
        
        if not self.is_active:
            return False, "El cupón no está activo"
        
        if self.status != self.CouponStatus.ACTIVE:
            return False, "El cupón no está disponible"
        
        if now < self.valid_from or now > self.valid_until:
            return False, "El cupón ha expirado"
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False, "El cupón ha alcanzado su límite de usos"
        
        if cart_total < self.min_purchase_amount:
            return False, f"La compra mínima debe ser de ${self.min_purchase_amount}"
        
        if user:
            if self.is_first_purchase_only:
                user_order_count = Order.objects.filter(buyer=user, status=Order.Status.PAID).count()
                if user_order_count > 0:
                    return False, "Este cupón es solo para tu primera compra"
        
        return True, "Válido"
    
    def calculate_discount(self, subtotal):
        """Calcula el descuento para un monto dado."""
        if self.coupon_type == self.CouponType.PERCENTAGE:
            discount = subtotal * (self.discount_value / 100)
        else:
            discount = self.discount_value
        
        if self.max_discount_amount:
            discount = min(discount, self.max_discount_amount)
        
        return min(discount, subtotal)


class Refund(models.Model):
    """Solicitudes de reembolso."""
    
    class RefundStatus(models.TextChoices):
        PENDING = 'pending', _('Pendiente')
        APPROVED = 'approved', _('Aprobado')
        REJECTED = 'rejected', _('Rechanzado')
        PROCESSED = 'processed', _('Procesado')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refunds')
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='refunds'
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    reason = models.TextField(_('razón'))
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=RefundStatus.choices,
        default=RefundStatus.PENDING
    )
    
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2)
    mercadopago_refund_id = models.CharField(max_length=100, blank=True)
    
    admin_notes = models.TextField(blank=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'refunds'
        verbose_name = _('reembolso')
        verbose_name_plural = _('reembolsos')
    
    def __str__(self):
        return f"Refund {self.id} - {self.order.order_number}"
