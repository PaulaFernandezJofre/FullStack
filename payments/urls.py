"""
URLs de Pagos
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import PayoutViewSet, TransactionViewSet, EarningsViewSet
from .mercadopago_views import (
    MercadoPagoCheckoutView,
    MercadoPagoSuccessView,
    mercadopago_webhook
)

router = DefaultRouter()
router.register('payouts', PayoutViewSet, basename='payouts')
router.register('transactions', TransactionViewSet, basename='transactions')
router.register('earnings', EarningsViewSet, basename='earnings')

urlpatterns = [
    path('', include(router.urls)),
    path('mercadopago/create-preference/', MercadoPagoCheckoutView.as_view(), name='mercadopago-checkout'),
    path('mercadopago/webhook/', mercadopago_webhook, name='mercadopago-webhook'),
    path('mercadopago/success/<uuid:order_id>/', MercadoPagoSuccessView.as_view(), name='mercadopago-success'),
]
