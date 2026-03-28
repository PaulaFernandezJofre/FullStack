"""
Modelos de Usuario con roles: Admin, Vendedor, Comprador
Sistema de autenticación personalizado
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField

import uuid


class User(AbstractUser):
    """
    Modelo de usuario extendido con roles específicos del marketplace.
    """
    
    class Role(models.TextChoices):
        ADMIN = 'admin', _('Administrador')
        SELLER = 'seller', _('Vendedor')
        BUYER = 'buyer', _('Comprador')
    
    class Status(models.TextChoices):
        ACTIVE = 'active', _('Activo')
        PENDING = 'pending', _('Pendiente de verificación')
        SUSPENDED = 'suspended', _('Suspendido')
        BANNED = 'banned', _('Bloqueado')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(
        _('rol'),
        max_length=20,
        choices=Role.choices,
        default=Role.BUYER
    )
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE
    )
    
    # Información personal
    phone = PhoneNumberField(_('teléfono'), blank=True, null=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(_('biografía'), blank=True, max_length=500)
    date_of_birth = models.DateField(_('fecha de nacimiento'), blank=True, null=True)
    
    # Información de vendedor
    company_name = models.CharField(_('nombre de empresa'), max_length=255, blank=True)
    tax_id = models.CharField(_('RUT/TIN'), max_length=20, blank=True)
    rut_verified = models.BooleanField(_('RUT verificado'), default=False)
    website = models.URLField(_('sitio web'), blank=True)
    
    # Verificación de cuenta
    email_verified = models.BooleanField(_('email verificado'), default=False)
    password_verified = models.BooleanField(_('contraseña verificada'), default=False)
    name_verified = models.BooleanField(_('nombres verificados'), default=False)
    account_verified = models.BooleanField(_('cuenta verificada'), default=False)
    
    # Configuración de pagos - Mercado Pago Chile
    mercadopago_email = models.EmailField(_('email Mercado Pago'), blank=True)
    mercadopago_customer_id = models.CharField(max_length=100, blank=True)
    mercadopago_seller_id = models.CharField(max_length=100, blank=True)
    mercadopago_verified = models.BooleanField(_('Mercado Pago verificado'), default=False)
    bank_account_verified = models.BooleanField(default=False)
    payout_method = models.CharField(
        _('método de pago'),
        max_length=20,
        choices=[
            ('mercadopago', 'Mercado Pago'),
            ('transfer', 'Transferencia bancaria'),
        ],
        default='mercadopago'
    )
    bank_name = models.CharField(_('nombre del banco'), max_length=100, blank=True)
    bank_account_number = models.CharField(_('número de cuenta'), max_length=50, blank=True)
    bank_clabe = models.CharField(_('CLABE interbancaria'), max_length=20, blank=True)
    bank_rut = models.CharField(_('RUT titular cuenta'), max_length=20, blank=True)
    
    # Preferencias
    language = models.CharField(max_length=10, default='es')
    currency = models.CharField(max_length=3, default='MXN')
    email_notifications = models.BooleanField(default=True)
    marketing_emails = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    email_verified_at = models.DateTimeField(blank=True, null=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('usuario')
        verbose_name_plural = _('usuarios')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['role', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.email})"
    
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    @property
    def is_seller(self):
        return self.role == self.Role.SELLER
    
    @property
    def is_buyer(self):
        return self.role == self.Role.BUYER
    
    @property
    def can_sell(self):
        return self.role in [self.Role.ADMIN, self.Role.SELLER]
    
    @property
    def is_verified_seller(self):
        return self.can_sell and self.bank_account_verified
    
    def get_display_name(self):
        if self.get_full_name():
            return self.get_full_name()
        return self.username
    
    def upgrade_to_seller(self):
        if self.role == self.Role.BUYER:
            self.role = self.Role.SELLER
            self.save(update_fields=['role', 'updated_at'])
            return True
        return False


class UserAddress(models.Model):
    """Direcciones de usuario para envíos y facturación."""
    
    class AddressType(models.TextChoices):
        SHIPPING = 'shipping', _('Envío')
        BILLING = 'billing', _('Facturación')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=20, choices=AddressType.choices, default=AddressType.SHIPPING)
    
    # Datos de dirección
    street = models.CharField(_('calle'), max_length=255)
    exterior_number = models.CharField(_('número exterior'), max_length=20, blank=True)
    interior_number = models.CharField(_('número interior'), max_length=20, blank=True)
    colony = models.CharField(_('colonia'), max_length=255)
    city = models.CharField(_('ciudad'), max_length=100)
    state = models.CharField(_('estado'), max_length=100)
    postal_code = models.CharField(_('código postal'), max_length=10)
    country = models.CharField(_('país'), max_length=100, default='México')
    
    # Datos fiscales (para facturación)
    company_name = models.CharField(_('razón social'), max_length=255, blank=True)
    tax_id = models.CharField(_('RFC'), max_length=20, blank=True)
    use_company_address = models.BooleanField(default=False)
    
    is_default = models.BooleanField(_('dirección principal'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_addresses'
        verbose_name = _('dirección')
        verbose_name_plural = _('direcciones')
        ordering = ['-is_default', '-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.address_type}: {self.street}"
    
    @property
    def full_address(self):
        parts = [self.street]
        if self.exterior_number:
            parts.append(f"#{self.exterior_number}")
        if self.interior_number:
            parts.append(f"Int. {self.interior_number}")
        parts.extend([self.colony, self.city, self.state, self.postal_code, self.country])
        return ', '.join(filter(None, parts))


class UserSession(models.Model):
    """Control de sesiones de usuario para seguridad."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    device_type = models.CharField(max_length=50)
    location = models.CharField(max_length=255, blank=True)
    last_active = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'user_sessions'
        verbose_name = _('sesión')
        verbose_name_plural = _('sesiones')
        ordering = ['-last_active']
    
    def __str__(self):
        return f"{self.user.email} - {self.device_type} - {self.last_active}"


class SellerStats(models.Model):
    """Estadísticas de vendedor para dashboard rápido."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_stats')
    
    # Productos
    total_products = models.PositiveIntegerField(default=0)
    active_products = models.PositiveIntegerField(default=0)
    pending_products = models.PositiveIntegerField(default=0)
    rejected_products = models.PositiveIntegerField(default=0)
    
    # Ventas
    total_sales = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_platform_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Ganancias disponibles
    available_earnings = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pending_payouts = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_paid_out = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Ratings
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Rankings
    total_views = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'seller_stats'
        verbose_name = _('estadística de vendedor')
        verbose_name_plural = _('estadísticas de vendedores')
    
    def __str__(self):
        return f"Stats de {self.user.email}"


class BuyerProfile(models.Model):
    """Perfil extendido para compradores."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    
    # Preferencias
    favorite_categories = models.ManyToManyField('products.Category', blank=True)
    language_preference = models.CharField(max_length=10, default='es')
    
    # Historial
    total_purchases = models.PositiveIntegerField(default=0)
    total_spent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    favorite_products = models.ManyToManyField('products.Product', blank=True)
    
    # Notificaciones
    notify_new_products = models.BooleanField(default=True)
    notify_price_drops = models.BooleanField(default=True)
    notify_seller_news = models.BooleanField(default=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'buyer_profiles'
        verbose_name = _('perfil de comprador')
        verbose_name_plural = _('perfiles de compradores')
    
    def __str__(self):
        return f"Perfil de {self.user.email}"
