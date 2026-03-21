"""
Modelos de Sistema de Soporte
Tickets y chat de ayuda
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

import uuid


class SupportTicket(models.Model):
    """
    Sistema de tickets de soporte.
    """
    
    class Priority(models.TextChoices):
        LOW = 'low', _('Baja')
        MEDIUM = 'medium', _('Media')
        HIGH = 'high', _('Alta')
        URGENT = 'urgent', _('Urgente')
    
    class Status(models.TextChoices):
        OPEN = 'open', _('Abierto')
        IN_PROGRESS = 'in_progress', _('En progreso')
        PENDING_RESPONSE = 'pending_response', _('Pendiente de respuesta')
        RESOLVED = 'resolved', _('Resuelto')
        CLOSED = 'closed', _('Cerrado')
    
    class Category(models.TextChoices):
        TECHNICAL = 'technical', _('Técnico')
        BILLING = 'billing', _('Facturación')
        SALES = 'sales', _('Ventas')
        ACCOUNT = 'account', _('Cuenta')
        PRODUCT_INQUIRY = 'product_inquiry', _('Consulta de producto')
        REFUND = 'refund', _('Reembolso')
        PARTNERSHIP = 'partnership', _('Alianzas')
        OTHER = 'other', _('Otro')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ticket_number = models.CharField(max_length=20, unique=True)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='support_tickets'
    )
    
    # Asignación
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tickets'
    )
    
    # Información
    category = models.CharField(
        _('categoría'),
        max_length=20,
        choices=Category.choices,
        default=Category.OTHER
    )
    priority = models.CharField(
        _('prioridad'),
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM
    )
    status = models.CharField(
        _('estado'),
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN
    )
    
    # Contenido
    subject = models.CharField(_('asunto'), max_length=300)
    description = models.TextField(_('descripción'))
    
    # Referencias
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_tickets'
    )
    related_product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='support_tickets'
    )
    
    # Archivos adjuntos
    attachments = models.JSONField(default=list, blank=True)
    
    # Respuesta rápida
    first_response_at = models.DateTimeField(blank=True, null=True)
    first_response_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='first_responses'
    )
    
    # Satisfacción
    satisfaction_rating = models.PositiveIntegerField(
        choices=[(i, f'{i} estrellas') for i in range(1, 6)],
        blank=True,
        null=True
    )
    satisfaction_comment = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    
    # IP
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        db_table = 'support_tickets'
        verbose_name = _('ticket')
        verbose_name_plural = _('tickets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ticket_number']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['assigned_to', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"[{self.ticket_number}] {self.subject}"
    
    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)
    
    def generate_ticket_number(self):
        last_ticket = SupportTicket.objects.order_by('created_at').first()
        if last_ticket:
            last_number = int(last_ticket.ticket_number.replace('TKT-', ''))
            new_number = last_number + 1
        else:
            new_number = 1
        return f"TKT-{new_number:06d}"
    
    @property
    def response_time(self):
        """Tiempo de respuesta en horas."""
        if self.first_response_at:
            delta = self.first_response_at - self.created_at
            return delta.total_seconds() / 3600
        return None
    
    @property
    def resolution_time(self):
        """Tiempo de resolución en horas."""
        if self.resolved_at:
            delta = self.resolved_at - self.created_at
            return delta.total_seconds() / 3600
        return None
    
    def mark_as_read(self, user):
        """Marcar como leído."""
        self.read_by.add(user)
    
    def close(self):
        """Cerrar ticket."""
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save()
    
    def resolve(self):
        """Resolver ticket."""
        self.status = self.Status.RESOLVED
        self.resolved_at = timezone.now()
        self.save()


class TicketMessage(models.Model):
    """Mensajes en tickets de soporte."""
    
    class MessageType(models.TextChoices):
        USER = 'user', _('Usuario')
        AGENT = 'agent', _('Agente')
        SYSTEM = 'system', _('Sistema')
        NOTE = 'note', _('Nota interna')
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ticket_messages'
    )
    
    message_type = models.CharField(
        _('tipo'),
        max_length=10,
        choices=MessageType.choices,
        default=MessageType.USER
    )
    
    content = models.TextField(_('contenido'))
    
    # Archivos adjuntos
    attachments = models.JSONField(default=list, blank=True)
    
    # Estado
    is_internal = models.BooleanField(
        _('nota interna'),
        default=False,
        help_text='Las notas internas solo son visibles para el staff'
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Editado
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'ticket_messages'
        verbose_name = _('mensaje')
        verbose_name_plural = _('mensajes')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
        ]
    
    def __str__(self):
        return f"Mensaje en {self.ticket.ticket_number} - {self.created_at}"


class TicketAttachment(models.Model):
    """Archivos adjuntos a tickets."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    ticket = models.ForeignKey(
        SupportTicket,
        on_delete=models.CASCADE,
        related_name='ticket_attachments',
        null=True
    )
    message = models.ForeignKey(
        TicketMessage,
        on_delete=models.CASCADE,
        related_name='ticket_attachments',
        null=True
    )
    
    file = models.FileField(upload_to='support/attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    mime_type = models.CharField(max_length=100)
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'ticket_attachments'
        verbose_name = _('adjunto')
        verbose_name_plural = _('adjuntos')


class KnowledgeBaseCategory(models.Model):
    """Categorías de la base de conocimiento."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    
    name = models.CharField(_('nombre'), max_length=100)
    slug = models.SlugField(_('slug'), unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'knowledge_base_categories'
        verbose_name = _('categoría KB')
        verbose_name_plural = _('categorías KB')
        ordering = ['order', 'name']
    
    def __str__(self):
        return self.name


class KnowledgeBaseArticle(models.Model):
    """Artículos de la base de conocimiento."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        KnowledgeBaseCategory,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles'
    )
    
    title = models.CharField(_('título'), max_length=200)
    slug = models.SlugField(_('slug'), unique=True)
    content = models.TextField()
    
    # SEO
    meta_title = models.CharField(max_length=70, blank=True)
    meta_description = models.TextField(max_length=160, blank=True)
    keywords = models.CharField(max_length=255, blank=True)
    
    # Estado
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    views = models.PositiveIntegerField(default=0)
    
    # Utilidad
    helpful_yes = models.PositiveIntegerField(default=0)
    helpful_no = models.PositiveIntegerField(default=0)
    
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='kb_articles'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'knowledge_base_articles'
        verbose_name = _('artículo KB')
        verbose_name_plural = _('artículos KB')
        ordering = ['-views', '-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def helpfulness(self):
        total = self.helpful_yes + self.helpful_no
        if total == 0:
            return 0
        return (self.helpful_yes / total) * 100


class FAQ(models.Model):
    """Preguntas frecuentes."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(
        KnowledgeBaseCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faqs'
    )
    
    question = models.CharField(_('pregunta'), max_length=500)
    answer = models.TextField(_('respuesta'))
    
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)
    views = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'faqs'
        verbose_name = _('pregunta frecuente')
        verbose_name_plural = _('preguntas frecuentes')
        ordering = ['order', 'question']
    
    def __str__(self):
        return self.question


class CannedResponse(models.Model):
    """Respuestas predefinidas para tickets."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    name = models.CharField(_('nombre'), max_length=100)
    category = models.CharField(
        _('categoría'),
        max_length=50,
        choices=[
            ('general', 'General'),
            ('technical', 'Técnico'),
            ('billing', 'Facturación'),
            ('refund', 'Reembolso'),
        ],
        default='general'
    )
    
    content = models.TextField(_('contenido'))
    is_active = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'canned_responses'
        verbose_name = _('respuesta predefinida')
        verbose_name_plural = _('respuestas predefinidas')
    
    def __str__(self):
        return self.name
