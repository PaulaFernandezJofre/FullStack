"""
Vistas de Soporte
"""

from django.views.generic import TemplateView, CreateView
from django.contrib import messages
from django.shortcuts import redirect
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import SupportTicket, TicketMessage, FAQ, KnowledgeBaseArticle
from .serializers import (
    SupportTicketSerializer, SupportTicketCreateSerializer,
    TicketMessageSerializer, FASerializer, KnowledgeBaseArticleSerializer
)


class IsAdminOrSupport(permissions.BasePermission):
    """Permite acceso a admins y personal de soporte."""
    
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_admin:
            return True
        return request.user.role in ['admin', 'seller']


class SupportTicketViewSet(viewsets.ModelViewSet):
    """Gestión de tickets de soporte."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return SupportTicketCreateSerializer
        return SupportTicketSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return SupportTicket.objects.all()
        return SupportTicket.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def reply(self, request, pk=None):
        """Agregar respuesta a ticket."""
        ticket = self.get_object()
        
        if ticket.status == SupportTicket.Status.CLOSED:
            return Response(
                {'error': 'El ticket está cerrado'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        message = TicketMessage.objects.create(
            ticket=ticket,
            sender=request.user,
            message_type=TicketMessage.MessageType.USER if request.user.is_buyer else TicketMessage.MessageType.AGENT,
            content=request.data.get('content', ''),
            attachments=request.data.get('attachments', [])
        )
        
        if not ticket.first_response_at and not request.user.is_buyer:
            ticket.first_response_at = timezone.now()
            ticket.first_response_by = request.user
            ticket.status = SupportTicket.Status.IN_PROGRESS
            ticket.save()
        
        return Response(
            TicketMessageSerializer(message).data,
            status=status.HTTP_201_CREATED
        )
    
    @action(detail=True, methods=['post'])
    def close(self, request, pk=None):
        """Cerrar ticket."""
        ticket = self.get_object()
        ticket.close()
        return Response({'status': 'closed'})
    
    @action(detail=True, methods=['post'])
    def rate(self, request, pk=None):
        """Calificar atención."""
        ticket = self.get_object()
        
        if ticket.status != SupportTicket.Status.RESOLVED and ticket.status != SupportTicket.Status.CLOSED:
            return Response(
                {'error': 'El ticket debe estar resuelto primero'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ticket.satisfaction_rating = request.data.get('rating')
        ticket.satisfaction_comment = request.data.get('comment', '')
        ticket.save()
        
        return Response({'status': 'rated'})


class FAQViewSet(viewsets.ReadOnlyModelViewSet):
    """FAQs públicos."""
    
    queryset = FAQ.objects.filter(is_published=True)
    serializer_class = FASerializer
    permission_classes = [permissions.AllowAny]


class KnowledgeBaseViewSet(viewsets.ReadOnlyModelViewSet):
    """Base de conocimiento."""
    
    serializer_class = KnowledgeBaseArticleSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        return KnowledgeBaseArticle.objects.filter(is_published=True)


class SupportTicketCreateView(CreateView):
    """Vista para crear tickets de soporte."""
    
    model = SupportTicket
    template_name = 'support/create_ticket.html'
    fields = ['subject', 'description', 'category', 'priority']
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para crear un ticket.')
            return redirect('account:login')
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.status = SupportTicket.Status.OPEN
        messages.success(self.request, 'Ticket creado exitosamente. Te responderemos pronto.')
        return super().form_valid(form)
    
    def get_success_url(self):
        return '/account/dashboard/'

