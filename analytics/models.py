"""
Modelos de Analítica y Estadísticas
Dashboard para el administrador
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

import uuid


class DailyStats(models.Model):
    """Estadísticas diarias agregadas."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(_('fecha'), unique=True)
    
    # Ventas
    total_orders = models.PositiveIntegerField(default=0)
    completed_orders = models.PositiveIntegerField(default=0)
    cancelled_orders = models.PositiveIntegerField(default=0)
    refunded_orders = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_platform_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_seller_payouts = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    # Productos
    new_products = models.PositiveIntegerField(default=0)
    approved_products = models.PositiveIntegerField(default=0)
    total_product_views = models.PositiveIntegerField(default=0)
    total_product_sales = models.PositiveIntegerField(default=0)
    
    # Usuarios
    new_users = models.PositiveIntegerField(default=0)
    new_sellers = models.PositiveIntegerField(default=0)
    new_buyers = models.PositiveIntegerField(default=0)
    active_users = models.PositiveIntegerField(default=0)
    
    # Tickets
    new_support_tickets = models.PositiveIntegerField(default=0)
    resolved_tickets = models.PositiveIntegerField(default=0)
    
    # Sitio
    total_page_views = models.PositiveIntegerField(default=0)
    unique_visitors = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'daily_stats'
        verbose_name = _('estadística diaria')
        verbose_name_plural = _('estadísticas diarias')
        ordering = ['-date']
    
    def __str__(self):
        return f"Stats {self.date}"


class ProductStats(models.Model):
    """Estadísticas por producto."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='stats'
    )
    
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    favorites = models.PositiveIntegerField(default=0)
    sales = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Período
    period_start = models.DateField()
    period_end = models.DateField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_stats'
        verbose_name = _('estadística de producto')
        verbose_name_plural = _('estadísticas de productos')


class CategoryStats(models.Model):
    """Estadísticas por categoría."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.OneToOneField(
        'products.Category',
        on_delete=models.CASCADE,
        related_name='stats'
    )
    
    total_products = models.PositiveIntegerField(default=0)
    total_sales = models.PositiveIntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    period_start = models.DateField()
    period_end = models.DateField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'category_stats'
        verbose_name = _('estadística de categoría')
        verbose_name_plural = _('estadísticas de categorías')


class SellerStats(models.Model):
    """Estadísticas por vendedor."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics'
    )
    
    total_revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_sales = models.PositiveIntegerField(default=0)
    total_products = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    
    period_start = models.DateField()
    period_end = models.DateField()
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'seller_analytics'
        verbose_name = _('analítica de vendedor')
        verbose_name_plural = _('analíticas de vendedores')


class PageView(models.Model):
    """Registro de vistas de página."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    path = models.CharField(max_length=500)
    view_name = models.CharField(max_length=200, blank=True)
    
    # UTM
    utm_source = models.CharField(max_length=200, blank=True)
    utm_medium = models.CharField(max_length=200, blank=True)
    utm_campaign = models.CharField(max_length=200, blank=True)
    utm_term = models.CharField(max_length=200, blank=True)
    utm_content = models.CharField(max_length=200, blank=True)
    
    # Navegador
    referrer = models.URLField(blank=True)
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField()
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    # Dispositivo
    device_type = models.CharField(
        max_length=20,
        choices=[
            ('desktop', 'Desktop'),
            ('mobile', 'Mobile'),
            ('tablet', 'Tablet'),
        ],
        default='desktop'
    )
    browser = models.CharField(max_length=100, blank=True)
    os = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'page_views'
        verbose_name = _('vista de página')
        verbose_name_plural = _('vistas de páginas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['path', 'created_at']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]


class SearchQuery(models.Model):
    """Búsquedas realizadas en el sitio."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    query = models.CharField(max_length=500)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    results_count = models.PositiveIntegerField(default=0)
    has_results = models.BooleanField(default=True)
    
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'search_queries'
        verbose_name = _('búsqueda')
        verbose_name_plural = _('búsquedas')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['query']),
            models.Index(fields=['created_at']),
        ]


class ConversionFunnel(models.Model):
    """Embudo de conversión."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField()
    
    # Etapas del embudo
    product_views = models.PositiveIntegerField(default=0)
    product_detail_views = models.PositiveIntegerField(default=0)
    add_to_cart = models.PositiveIntegerField(default=0)
    checkout_started = models.PositiveIntegerField(default=0)
    checkout_completed = models.PositiveIntegerField(default=0)
    
    # Tasas de conversión
    view_to_detail_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    detail_to_cart_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cart_to_checkout_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    checkout_to_sale_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    overall_conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'conversion_funnel'
        verbose_name = _('embudo de conversión')
        verbose_name_plural = _('embudos de conversión')
        unique_together = ['date']
        ordering = ['-date']


class GeographicStats(models.Model):
    """Estadísticas geográficas."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    date = models.DateField()
    country = models.CharField(max_length=100)
    region = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    
    visitors = models.PositiveIntegerField(default=0)
    page_views = models.PositiveIntegerField(default=0)
    orders = models.PositiveIntegerField(default=0)
    revenue = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'geographic_stats'
        verbose_name = _('estadística geográfica')
        verbose_name_plural = _('estadísticas geográficas')
        unique_together = ['date', 'country', 'region', 'city']
        ordering = ['-date', '-revenue']


class Report(models.Model):
    """Reportes generados."""
    
    class ReportType(models.TextChoices):
        SALES = 'sales', _('Ventas')
        REVENUE = 'revenue', _('Ingresos')
        PRODUCTS = 'products', _('Productos')
        USERS = 'users', _('Usuarios')
        PERFORMANCE = 'performance', _('Rendimiento')
        CUSTOM = 'custom', _('Personalizado')
    
    class ReportFormat(models.TextChoices):
        PDF = 'pdf', 'PDF'
        EXCEL = 'excel', 'Excel'
        CSV = 'csv', 'CSV'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    report_type = models.CharField(max_length=20, choices=ReportType.choices)
    format = models.CharField(max_length=10, choices=ReportFormat.choices, default=ReportFormat.PDF)
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    # Filtros
    start_date = models.DateField()
    end_date = models.DateField()
    filters = models.JSONField(default=dict, blank=True)
    
    # Archivo generado
    file = models.FileField(upload_to='reports/', blank=True, null=True)
    file_size = models.PositiveIntegerField(default=0)
    
    # Estado
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pendiente'),
            ('processing', 'Procesando'),
            ('completed', 'Completado'),
            ('failed', 'Fallido'),
        ],
        default='pending'
    )
    
    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'reports'
        verbose_name = _('reporte')
        verbose_name_plural = _('reportes')
        ordering = ['-created_at']
