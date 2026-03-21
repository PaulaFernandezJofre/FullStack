"""
Vistas de Productos
"""

from rest_framework import viewsets, status, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404

from .models import Product, Category, Tag, ProductImage, ProductFile, ProductReview
from .serializers import (
    ProductSerializer, ProductListSerializer, ProductDetailSerializer,
    ProductCreateSerializer, CategorySerializer, TagSerializer,
    ProductReviewSerializer, ProductReviewCreateSerializer
)
from .permissions import IsOwnerOrSeller


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para categorías."""
    
    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Obtiene el árbol de categorías."""
        root_categories = self.queryset.filter(parent__isnull=True)
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet para productos."""
    
    queryset = Product.objects.filter(status=Product.Status.APPROVED)
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'short_description', 'description', 'keywords']
    ordering_fields = ['price', 'created_at', 'sales', 'views', 'average_rating']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateSerializer
        elif self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductSerializer
    
    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.IsAuthenticated()]
        elif self.action in ['update', 'partial_update', 'delete']:
            return [IsOwnerOrSeller()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        product_type = self.request.query_params.get('type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        featured = self.request.query_params.get('featured')
        if featured == 'true':
            queryset = queryset.filter(is_featured=True)
        
        on_sale = self.request.query_params.get('on_sale')
        if on_sale == 'true':
            queryset = queryset.filter(is_on_sale=True)
        
        return queryset.select_related('category', 'seller').prefetch_related('images', 'tags')
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        instance.views += 1
        instance.save(update_fields=['views'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Productos destacados."""
        products = self.queryset.filter(is_featured=True)[:8]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def new(self, request):
        """Productos nuevos."""
        products = self.queryset.filter(is_new=True)[:8]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def best_sellers(self, request):
        """Productos más vendidos."""
        products = self.queryset.order_by('-sales')[:8]
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def related(self, request):
        """Productos relacionados."""
        slug = request.query_params.get('slug')
        if not slug:
            return Response({'error': 'Slug requerido'}, status=400)
        
        product = get_object_or_404(Product, slug=slug)
        products = self.queryset.filter(
            category=product.category
        ).exclude(id=product.id)[:6]
        
        serializer = ProductListSerializer(products, many=True, context={'request': request})
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def favorite(self, request, slug=None):
        """Agregar/quitar de favoritos."""
        product = self.get_object()
        favorite, created = product.favorited_by.get_or_create(user=request.user)
        
        if not created:
            favorite.delete()
            return Response({'status': 'removed', 'favorited': False})
        
        return Response({'status': 'added', 'favorited': True})
    
    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, slug=None):
        """Reseñas del producto."""
        product = self.get_object()
        
        if request.method == 'GET':
            reviews = product.reviews.filter(is_approved=True)
            page = self.paginate_queryset(reviews)
            if page is not None:
                serializer = ProductReviewSerializer(page, many=True, context={'request': request})
                return self.get_paginated_response(serializer.data)
            serializer = ProductReviewSerializer(reviews, many=True, context={'request': request})
            return Response(serializer.data)
        
        serializer = ProductReviewCreateSerializer(
            data=request.data,
            context={'request': request, 'product': product}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet para tags."""
    
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    lookup_field = 'slug'
    
    @action(detail=False, methods=['get'])
    def popular(self, request):
        """Tags populares."""
        tags = self.queryset.order_by('-usage_count')[:20]
        serializer = self.get_serializer(tags, many=True)
        return Response(serializer.data)


class MyProductsViewSet(viewsets.ModelViewSet):
    """Productos del vendedor actual."""
    
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Product.objects.filter(seller=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductCreateSerializer
