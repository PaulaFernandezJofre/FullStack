"""
DevStack - Marketplace de Proyectos de Programación
URL principal del proyecto
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView

from core.sitemaps import (
    ProductSitemap, 
    CategorySitemap, 
    StaticViewSitemap
)

sitemaps = {
    'products': ProductSitemap,
    'categories': CategorySitemap,
    'static': StaticViewSitemap,
}

urlpatterns = [
    # Home page
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # Account (login, signup)
    path('account/', include(('users.urls', 'account'), namespace='account')),
    
    # Products
    path('products/', include('products.urls')),
    
    # Orders
    path('orders/', include('orders.urls')),
    
    # Sellers
    path('seller/', include('products.urls')),
    
    # Core app pages
    path('', include('core.urls')),
    
    # Apps principales
    path('api/v1/users/', include('users.urls')),
    path('api/v1/products/', include('products.urls')),
    path('api/v1/orders/', include('orders.urls')),
    path('api/v1/payments/', include('payments.urls')),
    path('api/v1/analytics/', include('analytics.urls')),
    path('api/v1/support/', include('support.urls')),
    
    # Documentación de API
    path('api/docs/', TemplateView.as_view(
        template_name='docs/api_docs.html',
        extra_context={'schema_url': 'api-schema'}
    ), name='api-docs'),
    
    # Robots.txt y Sitemap
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain'
    )),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]

# Servir archivos estáticos y media en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Handler de error personalizado
handler404 = 'core.views.handler_404'
handler500 = 'core.views.handler_500'
handler403 = 'core.views.handler_403'
handler400 = 'core.views.handler_400'
