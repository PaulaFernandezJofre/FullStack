"""
Admin de Productos - Gestión completa del catálogo de productos
"""

from django.contrib import admin
from .models import Product, Category, Tag


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Administración de Categorías."""
    list_display = ('name', 'slug', 'order')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Administración de Etiquetas."""
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Administración de Productos."""
    list_display = ('name', 'seller', 'category', 'price', 'status')
    list_filter = ('status', 'category')
    search_fields = ('name', 'seller__email')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('status',)
