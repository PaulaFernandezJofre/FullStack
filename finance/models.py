"""
Modelos Financieros para LogicPerfect
Sistema completo de distribución de pagos y gestión de cuentas
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from decimal import Decimal

import uuid


class AccountType(models.TextChoices):
    """Tipos de cuentas del sistema"""
    IVA = 'iva', _('IVA Chile (19%)')
    MERCADO_PAGO = 'mercadopago', _('Comisión Mercado Pago')
    PLATFORM_MAINTENANCE = 'platform', _('Mantención Plataforma')
    SELLER_EARNINGS = 'seller', _('Ganancias Vendedor')
    PLATFORM_REVENUE = 'revenue', _('Ingresos Netos Plataforma')


class TransactionType(models.TextChoices):
    """Tipos de transacciones financieras"""
    SALE = 'sale', _('Venta')
    IVA_CHARGE = 'iva', _('Cobro IVA')
    MERCADO_PAGO_FEE = 'mp_fee', _('Comisión Mercado Pago')
    PLATFORM_FEE = 'platform_fee', _('Comisión Plataforma')
    SELLER_PAYOUT = 'seller_payout', _('Pago a Vendedor')
    PLATFORM_PROFIT = 'platform_profit', _('Ganancia Neta Plataforma')
    REFUND = 'refund', _('Reembolso')
    DEPOSIT = 'deposit', _('Depósito')


class TransactionStatus(models.TextChoices):
    """Estados de transacción"""
    PENDING = 'pending', _('Pendiente')
    COMPLETED = 'completed', _('Completado')
    FAILED = 'failed', _('Fallido')
    CANCELLED = 'cancelled', _('Cancelado')
    REFUNDED = 'refunded', _('Reembolsado')


class Account(models.Model):
    """
    Cuenta contable del sistema.
    Cada tipo de distribución tiene su propia cuenta.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    account_type = models.CharField(
        _('tipo de cuenta'),
        max_length=30,
        choices=AccountType.choices,
        unique=True
    )
    
    name = models.CharField(_('nombre'), max_length=100)
    description = models.TextField(_('descripción'), blank=True)
    
    # Configuración de porcentajes
    percentage = models.DecimalField(
        _('porcentaje'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0'))]
    )
    
    # Montos acumulados
    total_credits = models.DecimalField(
        _('total créditos'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_debits = models.DecimalField(
        _('total débitos'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    @property
    def balance(self):
        return self.total_credits - self.total_debits
    
    currency = models.CharField(max_length=3, default='CLP')
    is_active = models.BooleanField(_('activa'), default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finance_accounts'
        verbose_name = _('cuenta')
        verbose_name_plural = _('cuentas')
        ordering = ['account_type']
    
    def __str__(self):
        return f"{self.name} ({self.account_type}) - ${self.balance:,.2f}"
    
    @classmethod
    def initialize_accounts(cls):
        """Inicializa las cuentas del sistema con sus porcentajes."""
        accounts_data = [
            {
                'account_type': AccountType.IVA,
                'name': 'IVA Chile (19%)',
                'description': 'Impuesto al valor agregado - Para autoridades tributarias',
                'percentage': Decimal('19.00'),
            },
            {
                'account_type': AccountType.MERCADO_PAGO,
                'name': 'Comisión Mercado Pago',
                'description': 'Tarifa por procesamiento de pagos (~6%)',
                'percentage': Decimal('5.99'),
            },
            {
                'account_type': AccountType.PLATFORM_MAINTENANCE,
                'name': 'Ganancia Plataforma (15%)',
                'description': 'Ganancia neta de LogicPerfect - 15% de cada venta',
                'percentage': Decimal('15.00'),
            },
            {
                'account_type': AccountType.SELLER_EARNINGS,
                'name': 'Ganancias Vendedores',
                'description': 'Pago neto a vendedores (~64% de cada venta)',
                'percentage': Decimal('64.00'),
            },
        ]
        
        for data in accounts_data:
            cls.objects.update_or_create(
                account_type=data['account_type'],
                defaults=data
            )


class PaymentDistribution(models.Model):
    """
    Distribución detallada de cada pago.
    Registra cómo se divide el dinero de cada venta.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    distribution_number = models.CharField(max_length=30, unique=True)
    
    # Referencia a la orden
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='distributions'
    )
    order_item = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        related_name='distributions',
        null=True,
        blank=True
    )
    
    # Monto total de la venta
    gross_amount = models.DecimalField(
        _('monto bruto'),
        max_digits=12,
        decimal_places=2
    )
    
    # Distribución
    iva_amount = models.DecimalField(
        _('monto IVA'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    mercadopago_fee = models.DecimalField(
        _('comisión Mercado Pago'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    platform_fee = models.DecimalField(
        _('comisión plataforma'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    seller_amount = models.DecimalField(
        _('monto vendedor'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Categoría del producto
    category = models.ForeignKey(
        'products.Category',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='distributions'
    )
    
    currency = models.CharField(max_length=3, default='CLP')
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finance_distributions'
        verbose_name = _('distribución')
        verbose_name_plural = _('distribuciones')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Distribución {self.distribution_number} - ${self.gross_amount}"
    
    def save(self, *args, **kwargs):
        if not self.distribution_number:
            self.distribution_number = self.generate_distribution_number()
        super().save(*args, **kwargs)
    
    def generate_distribution_number(self):
        count = PaymentDistribution.objects.count()
        return f"DIST-{timezone.now().strftime('%Y%m%d')}-{count + 1:06d}"
    
    @classmethod
    def calculate_distribution(cls, gross_amount):
        """
        Calcula la distribución de un monto bruto.
        
        Distribución para $100.000 CLP:
        - IVA Chile (19%): ~$16.000 (gobierno)
        - Mercado Pago (~6%): ~$5.040 (procesamiento)
        - Plataforma (15%): $15.000 (ganancia neta LogicPerfect)
        - Vendedor (~64%): ~$63.960 (pago neto al vendedor)
        """
        # Tasas
        iva_rate = Decimal('0.19')
        mp_fee_rate = Decimal('0.0599')  # ~5.99%
        platform_rate = Decimal('0.15')  # 15% ganancia neta plataforma
        seller_rate = Decimal('0.64')   # ~64% para vendedor
        
        # IVA Chile (19%)
        iva = gross_amount * iva_rate / (Decimal('1') + iva_rate)
        
        # Mercado Pago (~6% sobre monto sin IVA)
        amount_without_iva = gross_amount - iva
        mercadopago = amount_without_iva * mp_fee_rate
        
        # Después de IVA y MP fee
        after_costs = amount_without_iva - mercadopago
        
        # Plataforma (15% del total = ganancia neta)
        platform_profit = gross_amount * platform_rate
        
        # Vendedor (el resto)
        seller = after_costs - platform_profit
        
        return {
            'gross_amount': gross_amount,
            'iva_amount': iva.quantize(Decimal('1')),
            'mercadopago_fee': mercadopago.quantize(Decimal('1')),
            'platform_fee': platform_profit.quantize(Decimal('1')),
            'seller_amount': seller.quantize(Decimal('1')),
            'iva_rate': iva_rate * 100,
            'mp_rate': mp_fee_rate * 100,
            'platform_rate': platform_rate * 100,
            'seller_rate': seller_rate * 100,
        }
    
    def complete_distribution(self):
        """Completa la distribución y actualiza las cuentas."""
        if self.status == TransactionStatus.COMPLETED:
            return
        
        # Actualizar cuentas
        self._update_account(AccountType.IVA, self.iva_amount, credit=True)
        self._update_account(AccountType.MERCADO_PAGO, self.mercadopago_fee, credit=True)
        self._update_account(AccountType.PLATFORM_MAINTENANCE, self.platform_fee, credit=True)
        self._update_account(AccountType.SELLER_EARNINGS, self.seller_amount, credit=True)
        
        self.status = TransactionStatus.COMPLETED
        self.save()
    
    def _update_account(self, account_type, amount, credit=True):
        account, _ = Account.objects.get_or_create(account_type=account_type)
        if credit:
            account.total_credits += amount
        else:
            account.total_debits += amount
        account.save()


class FinancialTransaction(models.Model):
    """
    Transacción financiera detallada.
    Cada movimiento de dinero se registra aquí.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_number = models.CharField(max_length=30, unique=True)
    
    transaction_type = models.CharField(
        _('tipo'),
        max_length=30,
        choices=TransactionType.choices
    )
    
    # Cuenta afectada
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    
    # Usuario relacionado (vendedor o comprador)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='finance_transactions',
        null=True,
        blank=True
    )
    
    # Distribución asociada
    distribution = models.ForeignKey(
        PaymentDistribution,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions'
    )
    
    # Monto
    amount = models.DecimalField(
        _('monto'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(max_length=3, default='CLP')
    
    # Descripción
    description = models.TextField(_('descripción'), blank=True)
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING
    )
    
    # Referencias externas
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='finance_transactions'
    )
    mercadopago_payment_id = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'finance_transactions'
        verbose_name = _('transacción financiera')
        verbose_name_plural = _('transacciones financieras')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['account', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.transaction_number} - {self.get_transaction_type_display()} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_number:
            self.transaction_number = self.generate_transaction_number()
        super().save(*args, **kwargs)
    
    def generate_transaction_number(self):
        count = FinancialTransaction.objects.count()
        return f"FTX-{timezone.now().strftime('%Y%m%d')}-{count + 1:06d}"
    
    def complete(self):
        """Marca la transacción como completada y actualiza la cuenta."""
        if self.status == TransactionStatus.COMPLETED:
            return
        
        if self.transaction_type in [TransactionType.SALE, TransactionType.DEPOSIT]:
            self.account.total_credits += self.amount
        else:
            self.account.total_debits += self.amount
        
        self.account.save()
        self.status = TransactionStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()


class PayoutRequest(models.Model):
    """
    Solicitud de pago a vendedor.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payout_number = models.CharField(max_length=30, unique=True)
    
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payout_requests'
    )
    
    # Montos
    gross_amount = models.DecimalField(
        _('monto bruto'),
        max_digits=12,
        decimal_places=2
    )
    net_amount = models.DecimalField(
        _('monto neto'),
        max_digits=12,
        decimal_places=2
    )
    
    # Método de pago
    payout_method = models.CharField(
        _('método de pago'),
        max_length=20,
        choices=[
            ('mercadopago', 'Mercado Pago'),
            ('bank_transfer', 'Transferencia bancaria'),
        ],
        default='mercadopago'
    )
    
    # Estado
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=[
            ('pending', _('Pendiente')),
            ('processing', _('Procesando')),
            ('completed', _('Completado')),
            ('failed', _('Fallido')),
            ('cancelled', _('Cancelado')),
        ],
        default='pending'
    )
    
    # Referencias
    mercadopago_payment_id = models.CharField(max_length=100, blank=True)
    bank_reference = models.CharField(max_length=100, blank=True)
    
    # Notas
    admin_notes = models.TextField(_('notas admin'), blank=True)
    failure_reason = models.TextField(_('razón de fallo'), blank=True)
    
    # Timestamps
    requested_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'finance_payouts'
        verbose_name = _('solicitud de pago')
        verbose_name_plural = _('solicitudes de pago')
        ordering = ['-requested_at']
    
    def __str__(self):
        return f"{self.payout_number} - {self.seller.email} - ${self.net_amount}"
    
    def save(self, *args, **kwargs):
        if not self.payout_number:
            count = PayoutRequest.objects.count()
            self.payout_number = f"PAY-{timezone.now().strftime('%Y%m%d')}-{count + 1:06d}"
        super().save(*args, **kwargs)


class CategoryFinancialSummary(models.Model):
    """
    Resumen financiero por categoría.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    category = models.OneToOneField(
        'products.Category',
        on_delete=models.CASCADE,
        related_name='financial_summary'
    )
    
    # Totales
    total_sales = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(
        _('ingresos totales'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_iva = models.DecimalField(
        _('total IVA'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_mercadopago_fees = models.DecimalField(
        _('total comisiones MP'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_platform_fees = models.DecimalField(
        _('total comisiones plataforma'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_seller_payouts = models.DecimalField(
        _('total pagos a vendedores'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Para el último período
    period_sales = models.PositiveIntegerField(default=0)
    period_revenue = models.DecimalField(
        _('ingresos del período'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'finance_category_summary'
        verbose_name = _('resumen por categoría')
        verbose_name_plural = _('resúmenes por categoría')
    
    def __str__(self):
        return f"Resumen {self.category.name} - ${self.total_revenue:,.2f}"
    
    @property
    def platform_profit(self):
        return self.total_iva + self.total_platform_fees
    
    @property
    def seller_rate(self):
        if self.total_revenue > 0:
            return (self.total_seller_payouts / self.total_revenue * 100).quantize(Decimal('0.01'))
        return Decimal('0.00')
