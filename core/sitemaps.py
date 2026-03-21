"""
Sitemaps
"""

from django.contrib.sitemaps import Sitemap
from products.models import Product
from products.models import Category


class ProductSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Product.objects.filter(status=Product.Status.APPROVED)
    
    def lastmod(self, obj):
        return obj.updated_at


class CategorySitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.6
    
    def items(self):
        return Category.objects.filter(is_active=True)


class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return ['home', 'products', 'about', 'contact']
    
    def location(self, item):
        if item == 'home':
            return '/'
        return f'/{item}/'
