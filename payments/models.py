"""
Modelos de Pagos y Transacciones
Sistema de pagos con Mercado Pago y gestión de comisiones
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator

import uuid


class Payout(models.Model):
    """
    Pagos a vendedores (retiros de ganancias).
    """
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendiente')
        PROCESSING = 'processing', _('Procesando')
        COMPLETED = 'completed', _('Completado')
        FAILED = 'failed', _('Fallido')
        CANCELLED = 'cancelled', _('Cancelado')
    
    class PayoutMethod(models.TextChoices):
        BANK_TRANSFER = 'bank_transfer', 'Transferencia bancaria'
        PAYPAL = 'paypal', 'PayPal'
        MERCADO_PAGO = 'mercadopago', 'Mercado Pago'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payout_number = models.CharField(max_length=30, unique=True)
    
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payouts'
    )
    
    amount = models.DecimalField(
        _('monto'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(1)]
    )
    currency = models.CharField(max_length=3, default='MXN')
    
    method = models.CharField(
        _('método'),
        max_length=20,
        choices=PayoutMethod.choices,
        default=PayoutMethod.BANK_TRANSFER
    )
    
    # Cuenta destino
    bank_name = models.CharField(_('banco'), max_length=100, blank=True)
    bank_account_last4 = models.CharField(_('últimos 4 dígitos'), max_length=4, blank=True)
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Notas
    notes = models.TextField(blank=True)
    admin_notes = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    
    # Fechas
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    # Ordenes incluidas
    orders = models.ManyToManyField('orders.Order', through='PayoutOrder')
    
    class Meta:
        db_table = 'payouts'
        verbose_name = _('pago')
        verbose_name_plural = _('pagos')
        ordering = ['-requested_at']
        indexes = [
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['requested_at']),
        ]
    
    def __str__(self):
        return f"Payout {self.payout_number} - {self.seller.email} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.payout_number:
            self.payout_number = self.generate_payout_number()
        super().save(*args, **kwargs)
    
    def generate_payout_number(self):
        last_payout = Payout.objects.filter(seller=self.seller).order_by('requested_at').first()
        if last_payout:
            last_number = int(last_payout.payout_number.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"PAY-{self.seller.id.hex[:8].upper()}-{new_number:06d}"
    
    def mark_as_processing(self):
        self.status = self.Status.PROCESSING
        self.save()
    
    def mark_as_completed(self, transfer_id=None):
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.save()
        
        # Actualizar estadísticas del vendedor
        self.seller.seller_stats.total_paid_out += self.amount
        self.seller.seller_stats.pending_payouts -= self.amount
        self.seller.seller_stats.save()
    
    def mark_as_failed(self, reason):
        self.status = self.Status.FAILED
        self.failure_reason = reason
        self.save()
        
        # Devolver el monto a las ganancias disponibles
        self.seller.seller_stats.pending_payouts -= self.amount
        self.seller.seller_stats.available_earnings += self.amount
        self.seller.seller_stats.save()


class PayoutOrder(models.Model):
    """Ordenes incluidas en un pago."""
    
    payout = models.ForeignKey(Payout, on_delete=models.CASCADE)
    order = models.ForeignKey('orders.Order', on_delete=models.CASCADE)
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    class Meta:
        db_table = 'payout_orders'
        unique_together = ['payout', 'order', 'order_item']


class Transaction(models.Model):
    """
    Registro de todas las transacciones financieras.
    """
    
    class TransactionType(models.TextChoices):
        SALE = 'sale', _('Venta')
        PLATFORM_FEE = 'platform_fee', _('Comisión de plataforma')
        PAYOUT = 'payout', _('Pago a vendedor')
        REFUND = 'refund', _('Reembolso')
        ADJUSTMENT = 'adjustment', _('Ajuste')
        WITHDRAWAL = 'withdrawal', _('Retiro')
    
    class Status(models.TextChoices):
        PENDING = 'pending', _('Pendiente')
        COMPLETED = 'completed', _('Completado')
        FAILED = 'failed', _('Fallido')
        CANCELLED = 'cancelled', _('Cancelado')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_number = models.CharField(max_length=30, unique=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True
    )
    
    transaction_type = models.CharField(
        _('tipo'),
        max_length=20,
        choices=TransactionType.choices
    )
    
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='MXN')
    
    # Referencias
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    payout = models.ForeignKey(
        'Payout',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Mercado Pago
    mercadopago_payment_id = models.CharField(max_length=100, blank=True)
    mercadopago_preference_id = models.CharField(max_length=100, blank=True)
    mercadopago_merchant_order_id = models.CharField(max_length=100, blank=True)
    
    # Descripción
    description = models.TextField(blank=True)
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Metadatos
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = _('transacción')
        verbose_name_plural = _('transacciones')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'transaction_type']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Transacción {self.transaction_number} - {self.transaction_type} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()
        super().save(*args, **kwargs)
    
    def generate_transaction_number(self):
        return f"TXN-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"


class SellerEarning(models.Model):
    """
    Registro detallado de ganancias por vendedor.
    """
    
    class Source(models.TextChoices):
        SALE = 'sale', _('Venta')
        REFUND = 'refund', _('Reembolso')
        ADJUSTMENT = 'adjustment', _('Ajuste')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='earnings'
    )
    
    source = models.CharField(
        _('fuente'),
        max_length=20,
        choices=Source.choices,
        default=Source.SALE
    )
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='seller_earnings'
    )
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='payment_seller_earnings'
    )
    
    gross_amount = models.DecimalField(_('monto bruto'), max_digits=12, decimal_places=2)
    commission_rate = models.DecimalField(_('tasa de comisión'), max_digits=5, decimal_places=4)
    commission_amount = models.DecimalField(_('comisión'), max_digits=12, decimal_places=2)
    net_amount = models.DecimalField(_('monto neto'), max_digits=12, decimal_places=2)
    
    currency = models.CharField(max_length=3, default='MXN')
    
    # Estado de disponibilidad
    is_available = models.BooleanField(_('disponible para retiro'), default=True)
    payout = models.ForeignKey(
        'Payout',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='earnings'
    )
    payout_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'seller_earnings'
        verbose_name = _('ganancia')
        verbose_name_plural = _('ganancias')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['seller', 'is_available']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Ganancia {self.seller.email} - ${self.net_amount}"


class PlatformRevenue(models.Model):
    """
    Registro de ingresos de la plataforma (comisiones).
    """
    
    class Source(models.TextChoices):
        SALE = 'sale', _('Venta')
        REFUND_FEE = 'refund_fee', _('Tarifa de reembolso')
        SUBSCRIPTION = 'subscription', _('Suscripción')
        OTHER = 'other', _('Otro')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    source = models.CharField(_('fuente'), max_length=20, choices=Source.choices)
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='platform_revenue'
    )
    
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2)
    net_amount = models.DecimalField(max_digits=12, decimal_places=2)
    
    currency = models.CharField(max_length=3, default='MXN')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'platform_revenue'
        verbose_name = _('ingreso de plataforma')
        verbose_name_plural = _('ingresos de plataforma')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Ingreso plataforma - {self.source} - ${self.net_amount}"


class PaymentMethod(models.Model):
    """
    Métodos de pago guardados del usuario.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    
    type = models.CharField(
        _('tipo'),
        max_length=20,
        choices=[
            ('card', 'Tarjeta'),
            ('bank', 'Cuenta bancaria'),
            ('mercadopago', 'Mercado Pago'),
        ]
    )
    
    # Mercado Pago
    mercadopago_payment_id = models.CharField(max_length=100, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    
    # Estado
    is_default = models.BooleanField(_('método predeterminado'), default=False)
    is_verified = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = _('método de pago')
        verbose_name_plural = _('métodos de pago')
    
    def __str__(self):
        if self.type == 'card':
            return f"{self.card_brand} ****{self.card_last4}"
        return f"Cuenta {self.type}"
