"""
URLs de Soporte
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SupportTicketViewSet, FAQViewSet, KnowledgeBaseViewSet, SupportTicketCreateView

app_name = 'support'

router = DefaultRouter()
router.register('tickets', SupportTicketViewSet, basename='tickets')
router.register('faqs', FAQViewSet, basename='faqs')
router.register('knowledge-base', KnowledgeBaseViewSet, basename='knowledge-base')

urlpatterns = [
    path('api/', include(router.urls)),
    path('create/', SupportTicketCreateView.as_view(), name='create-ticket'),
]
