"""
Modelos de Productos y Categorías
Sistema completo de gestión de productos del marketplace
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, FileExtensionValidator

import uuid


def product_upload_path(instance, filename):
    """Genera la ruta de subida para archivos de producto."""
    ext = filename.split('.')[-1]
    return f'products/{instance.seller.id}/{instance.slug}/{uuid.uuid4()}.{ext}'


def product_image_path(instance, filename):
    """Genera la ruta de subida para imágenes de producto."""
    ext = filename.split('.')[-1]
    return f'products/{instance.product.seller.id}/{instance.product.slug}/images/{uuid.uuid4()}.{ext}'


class Category(models.Model):
    """Categorías de productos del marketplace."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    name = models.CharField(_('nombre'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True, max_length=100)
    description = models.TextField(_('descripción'), blank=True)
    icon = models.CharField(_('ícono'), max_length=50, blank=True)
    image = models.ImageField(
        _('imagen'),
        upload_to='categories/',
        blank=True,
        null=True
    )
    
    # SEO
    meta_title = models.CharField(_('meta título'), max_length=70, blank=True)
    meta_description = models.TextField(_('meta descripción'), max_length=160, blank=True)
    
    # Configuración
    is_active = models.BooleanField(_('activo'), default=True)
    is_featured = models.BooleanField(_('destacado'), default=False)
    order = models.PositiveIntegerField(_('orden'), default=0)
    
    # Estadísticas
    products_count = models.PositiveIntegerField(default=0, editable=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = _('categoría')
        verbose_name_plural = _('categorías')
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active', 'order']),
        ]
    
    def __str__(self):
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name
    
    @property
    def full_path(self):
        if self.parent:
            return f"{self.parent.full_path} / {self.name}"
        return self.name
    
    def get_ancestors(self):
        ancestors = []
        current = self
        while current.parent:
            ancestors.insert(0, current.parent)
            current = current.parent
        return ancestors
    
    def get_descendants(self):
        descendants = []
        for child in self.children.filter(is_active=True):
            descendants.append(child)
            descendants.extend(child.get_descendants())
        return descendants


class Tag(models.Model):
    """Tags para productos."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('nombre'), max_length=50, unique=True)
    slug = models.SlugField(_('slug'), unique=True, max_length=50)
    usage_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'tags'
        verbose_name = _('etiqueta')
        verbose_name_plural = _('etiquetas')
        ordering = ['-usage_count', 'name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Modelo principal de producto del marketplace.
    """
    
    class Status(models.TextChoices):
        DRAFT = 'draft', _('Borrador')
        PENDING = 'pending', _('Pendiente de revisión')
        APPROVED = 'approved', _('Aprobado')
        REJECTED = 'rejected', _('Rechazado')
        ARCHIVED = 'archived', _('Archivado')
    
    class ProductType(models.TextChoices):
        SOFTWARE = 'software', _('Software')
        TEMPLATE = 'template', _('Template')
        COURSE = 'course', _('Curso/Clase')
        WEB_APP = 'web_app', _('Aplicación Web')
        MOBILE_APP = 'mobile_app', _('Aplicación Móvil')
        WEBSITE = 'website', _('Página Web')
        PLUGIN = 'plugin', _('Plugin/Extensión')
        COMPONENT = 'component', _('Componente')
        SCRIPT = 'script', _('Script')
        OTHER = 'other', _('Otro')
    
    class LicenseType(models.TextChoices):
        REGULAR = 'regular', _('Licencia Regular')
        EXTENDED = 'extended', _('Licencia Extendida')
        COMMERCIAL = 'commercial', _('Licencia Comercial')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='products'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='products'
    )
    
    # Información básica
    name = models.CharField(_('nombre'), max_length=200)
    slug = models.SlugField(_('slug'), max_length=200)
    short_description = models.CharField(_('descripción corta'), max_length=300)
    description = models.TextField(_('descripción completa'))
    
    # Tipo y características
    product_type = models.CharField(
        _('tipo de producto'),
        max_length=20,
        choices=ProductType.choices,
        default=ProductType.SOFTWARE
    )
    license_type = models.CharField(
        _('tipo de licencia'),
        max_length=20,
        choices=LicenseType.choices,
        default=LicenseType.REGULAR
    )
    
    # Precios
    price = models.DecimalField(
        _('precio'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    compare_at_price = models.DecimalField(
        _('precio anterior'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    discount_percentage = models.PositiveIntegerField(default=0)
    
    # Archivos y descargas
    file = models.FileField(
        _('archivo principal'),
        upload_to=product_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(
            allowed_extensions=['zip', 'rar', '7z', 'tar', 'gz', 'pdf', 'exe', 'dmg']
        )]
    )
    demo_file = models.FileField(
        _('demo/preview'),
        upload_to=product_upload_path,
        blank=True,
        null=True
    )
    demo_url = models.URLField(_('URL de demo'), blank=True)
    
    # Características del producto
    version = models.CharField(_('versión'), max_length=20, blank=True)
    release_date = models.DateField(_('fecha de lanzamiento'), blank=True, null=True)
    last_update = models.DateField(_('última actualización'), blank=True, null=True)
    changelog = models.TextField(_('historial de cambios'), blank=True)
    
    # Tecnologías
    technologies = models.JSONField(_('tecnologías'), default=list, blank=True)
    frameworks = models.JSONField(_('frameworks'), default=list, blank=True)
    languages = models.JSONField(_('lenguajes'), default=list, blank=True)
    
    # Requisitos
    requirements = models.JSONField(_('requisitos'), default=dict, blank=True)
    supported_browsers = models.JSONField(_('navegadores soportados'), default=list, blank=True)
    supported_os = models.JSONField(_('sistemas operativos'), default=list, blank=True)
    
    # SEO
    meta_title = models.CharField(_('meta título'), max_length=70, blank=True)
    meta_description = models.TextField(_('meta descripción'), max_length=160, blank=True)
    keywords = models.CharField(_('palabras clave'), max_length=255, blank=True)
    
    # Multimedia
    thumbnail = models.ImageField(
        _('miniatura'),
        upload_to='products/thumbnails/',
        blank=True,
        null=True
    )
    
    # Estado y moderación
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    rejection_reason = models.TextField(_('razón de rechazo'), blank=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_products'
    )
    
    # Configuración
    is_featured = models.BooleanField(_('destacado'), default=False)
    is_new = models.BooleanField(_('es nuevo'), default=True)
    is_on_sale = models.BooleanField(_('en oferta'), default=False)
    allow_comments = models.BooleanField(_('permitir comentarios'), default=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    # Licencias disponibles y precios
    has_regular_license = models.BooleanField(default=True)
    regular_license_price = models.DecimalField(
        _('precio licencia regular'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    has_extended_license = models.BooleanField(default=False)
    extended_license_price = models.DecimalField(
        _('precio licencia extendida'),
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )
    
    # Tags
    tags = models.ManyToManyField(Tag, blank=True, related_name='products')
    
    # Estadísticas
    views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    downloads = models.PositiveIntegerField(default=0)
    sales = models.PositiveIntegerField(default=0)
    favorites = models.PositiveIntegerField(default=0)
    conversion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = _('producto')
        verbose_name_plural = _('productos')
        ordering = ['-created_at']
        unique_together = ['seller', 'slug']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['status', 'is_featured']),
            models.Index(fields=['price', 'is_on_sale']),
            models.Index(fields=['seller', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        
        if self.compare_at_price and self.price < self.compare_at_price:
            discount = ((self.compare_at_price - self.price) / self.compare_at_price) * 100
            self.discount_percentage = int(discount)
        
        if self.status == self.Status.APPROVED and not self.published_at:
            self.published_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def current_price(self):
        if self.is_on_sale and self.compare_at_price:
            return self.price
        return self.price
    
    @property
    def final_price(self):
        return self.price
    
    @property
    def seller_earnings(self):
        from django.conf import settings
        commission = settings.PLATFORM_COMMISSION_RATE
        return self.final_price * (1 - commission)
    
    @property
    def platform_commission(self):
        from django.conf import settings
        return self.final_price * settings.PLATFORM_COMMISSION_RATE
    
    def get_absolute_url(self):
        return f"/products/{self.category.slug}/{self.slug}/"
    
    def get_demo_url(self):
        if self.demo_url:
            return self.demo_url
        if self.demo_file:
            return self.demo_file.url
        return None


class ProductImage(models.Model):
    """Imágenes adicionales de productos."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('imagen'), upload_to=product_image_path)
    alt_text = models.CharField(_('texto alternativo'), max_length=200, blank=True)
    order = models.PositiveIntegerField(_('orden'), default=0)
    is_primary = models.BooleanField(_('imagen principal'), default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_images'
        verbose_name = _('imagen de producto')
        verbose_name_plural = _('imágenes de productos')
        ordering = ['order', '-is_primary']
    
    def __str__(self):
        return f"{self.product.name} - Imagen {self.order}"


class ProductFile(models.Model):
    """Archivos adicionales de productos (documentación, etc)."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='files')
    name = models.CharField(_('nombre'), max_length=100)
    file = models.FileField(upload_to=product_upload_path)
    file_type = models.CharField(_('tipo'), max_length=50, blank=True)
    file_size = models.PositiveIntegerField(_('tamaño (bytes)'), default=0)
    is_downloadable = models.BooleanField(_('descargable'), default=True)
    order = models.PositiveIntegerField(_('orden'), default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'product_files'
        verbose_name = _('archivo de producto')
        verbose_name_plural = _('archivos de productos')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
            self.file_type = self.file.name.split('.')[-1].upper()
        super().save(*args, **kwargs)


class ProductReview(models.Model):
    """Reseñas de productos."""
    
    class Rating(models.IntegerChoices):
        ONE = 1, '1 - Muy malo'
        TWO = 2, '2 - Malo'
        THREE = 3, '3 - Regular'
        FOUR = 4, '4 - Bueno'
        FIVE = 5, '5 - Excelente'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='product_reviews'
    )
    order = models.ForeignKey(
        'orders.OrderItem',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='review'
    )
    
    rating = models.IntegerField(_('calificación'), choices=Rating.choices)
    title = models.CharField(_('título'), max_length=200, blank=True)
    comment = models.TextField(_('comentario'))
    
    # Ventajas y desventajas
    pros = models.JSONField(_('ventajas'), default=list, blank=True)
    cons = models.JSONField(_('desventajas'), default=list, blank=True)
    
    # Uso del producto
    used_for = models.CharField(_('uso del producto'), max_length=100, blank=True)
    expertise_level = models.CharField(
        _('nivel de experiencia'),
        max_length=20,
        choices=[
            ('beginner', 'Principiante'),
            ('intermediate', 'Intermedio'),
            ('advanced', 'Avanzado'),
        ],
        blank=True
    )
    
    # Estado
    is_approved = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    helpful_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'product_reviews'
        verbose_name = _('reseña')
        verbose_name_plural = _('reseñas')
        ordering = ['-created_at']
        unique_together = ['product', 'user']
    
    def __str__(self):
        return f"{self.user.email} - {self.product.name} - {self.rating}★"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.product.update_average_rating()


class ReviewHelpfulness(models.Model):
    """Votos de utilidad en reseñas."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    review = models.ForeignKey(ProductReview, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_helpful = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'review_helpfulness'
        unique_together = ['review', 'user']


class UserFavorite(models.Model):
    """Productos favoritos de usuarios."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'user_favorites'
        unique_together = ['user', 'product']
        verbose_name = _('favorito')
        verbose_name_plural = _('favoritos')


from django.utils.text import slugify
