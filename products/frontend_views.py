"""
Frontend Views para Productos
"""

from django.views.generic import ListView, DetailView, CreateView
from django.shortcuts import get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages

from .models import Product, Category
from .forms import ProductForm


class ProductListView(ListView):
    """Lista de productos."""
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Product.objects.filter(status=Product.Status.APPROVED).order_by('-created_at')
        
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        product_type = self.kwargs.get('product_type') or self.request.GET.get('type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['product_type'] = self.kwargs.get('product_type') or self.request.GET.get('type', '')
        return context


class ProductDetailView(DetailView):
    """Detalle de producto."""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(status=Product.Status.APPROVED)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            status=Product.Status.APPROVED
        ).exclude(id=self.object.id)[:4]
        return context


class CategoryProductsView(ListView):
    """Productos por categoría."""
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'], is_active=True)
        return Product.objects.filter(
            category=self.category,
            status=Product.Status.APPROVED
        ).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.filter(is_active=True)
        return context


class ProductCreateView(LoginRequiredMixin, CreateView):
    """Crear nuevo producto."""
    model = Product
    form_class = ProductForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('my-products')
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_seller and not request.user.is_admin:
            from django.shortcuts import redirect
            return redirect('dashboard')
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.seller = self.request.user
        form.instance.status = Product.Status.PENDING
        messages.success(self.request, 'Producto creado exitosamente. Será revisado por un administrador.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        return context
