"""
Serializers de Producto
"""

from rest_framework import serializers
from .models import Product, Category, Tag, ProductImage, ProductFile, ProductReview


class CategorySerializer(serializers.ModelSerializer):
    """Serializer de categoría."""
    
    product_count = serializers.SerializerMethodField()
    subcategories = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'icon', 'image',
            'parent', 'product_count', 'subcategories',
            'is_active', 'is_featured', 'order'
        ]
    
    def get_product_count(self, obj):
        return obj.products.filter(status=Product.Status.APPROVED).count()
    
    def get_subcategories(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class TagSerializer(serializers.ModelSerializer):
    """Serializer de tag."""
    
    class Meta:
        model = Tag
        fields = ['id', 'name', 'slug', 'usage_count']


class ProductImageSerializer(serializers.ModelSerializer):
    """Serializer de imagen de producto."""
    
    url = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductImage
        fields = ['id', 'url', 'alt_text', 'order', 'is_primary']
    
    def get_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None


class ProductFileSerializer(serializers.ModelSerializer):
    """Serializer de archivo de producto."""
    
    url = serializers.SerializerMethodField()
    file_size_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductFile
        fields = [
            'id', 'name', 'url', 'file_type', 'file_size',
            'file_size_formatted', 'is_downloadable', 'order'
        ]
    
    def get_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_file_size_formatted(self, obj):
        size = obj.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer para lista de productos."""
    
    category = CategorySerializer(read_only=True)
    seller_name = serializers.SerializerMethodField()
    seller_avatar = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description',
            'category', 'seller_name', 'seller_avatar',
            'price', 'compare_at_price', 'discount_percentage',
            'is_on_sale', 'thumbnail_url', 'product_type',
            'views', 'sales', 'average_rating', 'review_count',
            'is_favorited', 'is_featured', 'is_new', 'created_at'
        ]
    
    def get_seller_name(self, obj):
        return obj.seller.get_display_name()
    
    def get_seller_avatar(self, obj):
        if obj.seller.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.seller.avatar.url)
            return obj.seller.avatar.url
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.thumbnail.url)
            return obj.thumbnail.url
        return None
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer detalle de producto."""
    
    category = CategorySerializer(read_only=True)
    seller = serializers.SerializerMethodField()
    images = ProductImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    files = ProductFileSerializer(many=True, read_only=True)
    review_count = serializers.SerializerMethodField()
    reviews = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    demo_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'description',
            'category', 'seller', 'product_type', 'license_type',
            'price', 'compare_at_price', 'discount_percentage',
            'is_on_sale', 'thumbnail', 'images',
            'version', 'release_date', 'last_update', 'changelog',
            'technologies', 'frameworks', 'languages',
            'requirements', 'supported_browsers', 'supported_os',
            'tags', 'files', 'demo_url',
            'views', 'unique_views', 'downloads', 'sales',
            'average_rating', 'review_count', 'reviews',
            'is_favorited', 'is_featured', 'is_new',
            'has_regular_license', 'has_extended_license',
            'regular_license_price', 'extended_license_price',
            'meta_title', 'meta_description', 'keywords',
            'allow_comments', 'created_at', 'updated_at', 'published_at'
        ]
    
    def get_seller(self, obj):
        return {
            'id': str(obj.seller.id),
            'name': obj.seller.get_display_name(),
            'avatar': obj.seller.avatar.url if obj.seller.avatar else None,
            'company_name': obj.seller.company_name,
            'website': obj.seller.website,
            'rating': float(obj.seller.seller_stats.average_rating) if hasattr(obj.seller, 'seller_stats') else 0,
            'total_sales': obj.seller.seller_stats.total_sales if hasattr(obj.seller, 'seller_stats') else 0,
        }
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_reviews(self, obj):
        reviews = obj.reviews.filter(is_approved=True)[:5]
        return ProductReviewSerializer(reviews, many=True, context=self.context).data
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False
    
    def get_demo_url(self, obj):
        return obj.get_demo_url()


class ProductCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear/editar producto."""
    
    category_id = serializers.UUIDField(write_only=True, required=False)
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'description',
            'category_id', 'product_type', 'license_type',
            'price', 'compare_at_price',
            'file', 'demo_file', 'demo_url',
            'version', 'release_date', 'changelog',
            'technologies', 'frameworks', 'languages',
            'requirements', 'supported_browsers', 'supported_os',
            'meta_title', 'meta_description', 'keywords',
            'thumbnail', 'is_featured', 'is_new', 'allow_comments',
            'has_regular_license', 'has_extended_license',
            'regular_license_price', 'extended_license_price',
            'status'
        ]
    
    def create(self, validated_data):
        category_id = validated_data.pop('category_id', None)
        validated_data['seller'] = self.context['request'].user
        
        if category_id:
            try:
                validated_data['category'] = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        category_id = validated_data.pop('category_id', None)
        
        if category_id:
            try:
                validated_data['category'] = Category.objects.get(id=category_id)
            except Category.DoesNotExist:
                pass
        
        return super().update(instance, validated_data)


class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer de reseña de producto."""
    
    user_name = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    helpful_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'rating', 'title', 'comment',
            'pros', 'cons', 'used_for', 'expertise_level',
            'user_name', 'user_avatar',
            'helpful_count', 'helpful_yes', 'helpful_no',
            'is_featured', 'created_at'
        ]
    
    def get_user_name(self, obj):
        return obj.user.get_display_name()
    
    def get_user_avatar(self, obj):
        if obj.user.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.user.avatar.url)
            return obj.user.avatar.url
        return None
    
    def get_helpful_count(self, obj):
        return obj.helpful_count


class ProductReviewCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear reseña."""
    
    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment', 'pros', 'cons', 'used_for', 'expertise_level']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('La calificación debe estar entre 1 y 5.')
        return value
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        validated_data['product'] = self.context['product']
        
        order = self.context.get('order')
        if order:
            validated_data['order'] = order
        
        return super().create(validated_data)


class ProductSerializer(serializers.ModelSerializer):
    """Serializer base para productos."""
    
    class Meta:
        model = Product
        fields = '__all__'
