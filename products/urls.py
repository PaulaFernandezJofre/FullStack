"""
URLs de Productos
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, CategoryViewSet, TagViewSet, MyProductsViewSet
from .frontend_views import ProductListView, ProductDetailView, CategoryProductsView, ProductCreateView

router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register('tags', TagViewSet, basename='tags')
router.register('my-products', MyProductsViewSet, basename='my-products')
router.register('', ProductViewSet, basename='products')

urlpatterns = [
    # Frontend URLs
    path('', ProductListView.as_view(), name='product-list'),
    path('create/', ProductCreateView.as_view(), name='product-create'),
    path('type/<str:product_type>/', ProductListView.as_view(), name='product-type'),
    path('detail/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('category/<slug:slug>/', CategoryProductsView.as_view(), name='category-products'),
    
    # API URLs
    path('api/', include(router.urls)),
]
