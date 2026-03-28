"""
URLs de Órdenes
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register('api/cart', views.CartViewSet, basename='cart')
router.register('api/orders', views.OrderViewSet, basename='orders')
router.register('api/downloads', views.DownloadViewSet, basename='downloads')
router.register('api/coupons', views.CouponViewSet, basename='coupons')

urlpatterns = [
    # Frontend
    path('checkout/', views.CheckoutTemplateView.as_view(), name='checkout'),
    path('checkout/process/', views.CheckoutProcessView.as_view(), name='checkout-process'),
    path('cart/', views.CartTemplateView.as_view(), name='cart'),
    path('cart/remove/<uuid:item_id>/', views.CartRemoveItemView.as_view(), name='cart-remove'),
    path('apply-coupon/', views.ApplyCouponView.as_view(), name='apply-coupon'),
    
    # PDF Downloads
    path('admin/order/<uuid:order_id>/pdf/', views.download_order_pdf, name='order-pdf-download'),
    path('order/<uuid:order_id>/pdf/', views.view_order_pdf, name='order-pdf-view'),
    path('seller/report/pdf/', views.SellerReportPDFView.as_view(), name='seller-report-pdf'),
    
    # API
    path('', include(router.urls)),
]
