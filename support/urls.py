"""
URLs de Soporte
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import SupportTicketViewSet, FAQViewSet, KnowledgeBaseViewSet

router = DefaultRouter()
router.register('tickets', SupportTicketViewSet, basename='tickets')
router.register('faqs', FAQViewSet, basename='faqs')
router.register('knowledge-base', KnowledgeBaseViewSet, basename='knowledge-base')

urlpatterns = [
    path('', include(router.urls)),
]
