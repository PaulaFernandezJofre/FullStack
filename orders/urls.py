"""
URLs de Órdenes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import CartViewSet, OrderViewSet, DownloadViewSet, CouponViewSet, CheckoutTemplateView

router = DefaultRouter()
router.register('api/cart', CartViewSet, basename='cart')
router.register('api/orders', OrderViewSet, basename='orders')
router.register('api/downloads', DownloadViewSet, basename='downloads')
router.register('api/coupons', CouponViewSet, basename='coupons')

urlpatterns = [
    # Frontend
    path('checkout/', CheckoutTemplateView.as_view(), name='checkout'),
    path('cart/', CheckoutTemplateView.as_view(), name='cart'),
    
    # API
    path('', include(router.urls)),
]
