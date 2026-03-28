"""
Admin de Productos - Gestión completa del catálogo de productos
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import Product, Category, Tag, ProductReview, ReviewHelpfulness, UserFavorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'order')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'seller', 'category', 'price_display', 'rating_display',
        'favorites_count', 'status'
    )
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('name', 'seller__email', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at', 'total_reviews', 'average_rating')
    
    actions = ['approve_products', 'reject_products', 'feature_products', 'unfeature_products']
    
    def price_display(self, obj):
        if obj.discount_price:
            return format_html(
                '<span style="text-decoration: line-through; color: #888;">${}</span> '
                '<span style="color: #3ddc84;">${}</span>',
                obj.price, obj.discount_price
            )
        return f"${obj.price}"
    price_display.short_description = 'Precio'
    
    def rating_display(self, obj):
        if obj.total_reviews > 0:
            stars = '★' * int(obj.average_rating)
            empty = '☆' * (5 - int(obj.average_rating))
            return format_html(
                '<span style="color: #ffc107;">{}{}</span> '
                '<small style="color: #888;">({})</small>',
                stars, empty, obj.total_reviews
            )
        return format_html('<span style="color: #888;">Sin reseñas</span>')
    rating_display.short_description = 'Rating'
    
    def favorites_count(self, obj):
        count = obj.favorited_by.count()
        return format_html(
            '<span style="color: #ff69b4;"><i class="bi bi-heart-fill"></i> {}</span>',
            count
        )
    favorites_count.short_description = 'Favoritos'
    
    def approve_products(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} productos aprobados.')
    approve_products.short_description = 'Aprobar productos seleccionados'
    
    def reject_products(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} productos rechazados.')
    reject_products.short_description = 'Rechazar productos seleccionados'
    
    def feature_products(self, request, queryset):
        updated = queryset.update(featured=True)
        self.message_user(request, f'{updated} productos marcados como destacados.')
    feature_products.short_description = 'Marcar como destacados'
    
    def unfeature_products(self, request, queryset):
        updated = queryset.update(featured=False)
        self.message_user(request, f'{updated} productos desmarcados.')
    unfeature_products.short_description = 'Desmarcar como destacados'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = (
        'product_link', 'user_link', 'rating_stars', 'is_approved_badge',
        'helpful_count', 'created_date'
    )
    list_filter = ('is_approved', 'is_featured', 'rating', 'created_at')
    search_fields = ('product__name', 'user__email', 'comment')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    
    actions = ['approve_reviews', 'reject_reviews', 'feature_reviews']
    
    fieldsets = (
        ('Información', {
            'fields': ('product', 'user', 'order', 'rating')
        }),
        ('Contenido', {
            'fields': ('title', 'comment', 'pros', 'cons')
        }),
        ('Uso del Producto', {
            'fields': ('used_for', 'expertise_level'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('is_approved', 'is_featured', 'helpful_count')
        }),
        ('Fechas', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def product_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name[:30])
    product_link.short_description = 'Producto'
    
    def user_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Usuario'
    
    def rating_stars(self, obj):
        stars = '★' * obj.rating
        empty = '☆' * (5 - obj.rating)
        return format_html('<span style="color: #ffc107;">{}{}</span>', stars, empty)
    rating_stars.short_description = 'Rating'
    
    def is_approved_badge(self, obj):
        if obj.is_approved:
            return format_html('<i class="bi bi-check-circle-fill text-success"></i>')
        return format_html('<i class="bi bi-clock text-warning"></i>')
    is_approved_badge.short_description = 'Aprobada'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%d/%m/%Y')
    created_date.short_description = 'Fecha'
    
    def approve_reviews(self, request, queryset):
        for review in queryset.filter(is_approved=False):
            review.is_approved = True
            review.save()
            review.product.update_average_rating()
        self.message_user(request, f'{queryset.count()} reseñas aprobadas.')
    approve_reviews.short_description = 'Aprobar reseñas seleccionadas'
    
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f'{queryset.count()} reseñas rechazadas.')
    reject_reviews.short_description = 'Rechazar reseñas seleccionadas'
    
    def feature_reviews(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} reseñas destacadas.')
    feature_reviews.short_description = 'Destacar reseñas seleccionadas'


@admin.register(ReviewHelpfulness)
class ReviewHelpfulnessAdmin(admin.ModelAdmin):
    list_display = ('review_link', 'user_link', 'is_helpful', 'created_date')
    list_filter = ('is_helpful', 'created_at')
    search_fields = ('review__product__name', 'user__email')
    
    def review_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:products_productreview_change', args=[obj.review.id])
        return format_html('<a href="{}">Reseña #{}</a>', url, str(obj.review.id)[:8])
    review_link.short_description = 'Reseña'
    
    def user_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Usuario'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_date.short_description = 'Fecha'


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'product_link', 'created_date')
    list_filter = ('created_at',)
    search_fields = ('user__email', 'product__name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    
    def user_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:users_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.email)
    user_link.short_description = 'Usuario'
    
    def product_link(self, obj):
        from django.urls import reverse
        url = reverse('admin:products_product_change', args=[obj.product.id])
        return format_html('<a href="{}">{}</a>', url, obj.product.name[:40])
    product_link.short_description = 'Producto'
    
    def created_date(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_date.short_description = 'Fecha'
