"""
Serializers de Usuario
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuarios."""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'password_confirm',
            'first_name', 'last_name', 'role', 'phone'
        ]
        extra_kwargs = {
            'email': {'required': True},
            'username': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'role': {'required': False},
            'phone': {'required': False},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer principal de usuario."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'full_name', 'role', 'status', 'avatar', 'bio',
            'phone', 'company_name', 'website', 'language',
            'currency', 'email_notifications', 'marketing_emails',
            'created_at', 'last_login'
        ]
        read_only_fields = ['id', 'email', 'role', 'status', 'created_at', 'last_login']
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserPublicSerializer(serializers.ModelSerializer):
    """Serializer público de usuario (para perfiles)."""
    
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'first_name', 'last_name', 'full_name',
            'avatar', 'bio', 'company_name', 'website', 'created_at'
        ]
    
    def get_full_name(self, obj):
        return obj.get_full_name() or obj.username


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer para el perfil del usuario."""
    
    user = UserSerializer(read_only=True)
    seller_stats = serializers.SerializerMethodField()
    buyer_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'role', 'status', 'avatar', 'bio', 'phone',
            'company_name', 'tax_id', 'website', 'language',
            'currency', 'email_notifications', 'marketing_emails',
            'mercadopago_seller_id', 'bank_account_verified',
            'seller_stats', 'buyer_stats', 'created_at'
        ]
    
    def get_seller_stats(self, obj):
        if obj.can_sell:
            try:
                stats = obj.seller_stats
                return {
                    'total_products': stats.total_products,
                    'active_products': stats.active_products,
                    'total_sales': stats.total_sales,
                    'total_earnings': float(stats.total_earnings),
                    'available_earnings': float(stats.available_earnings),
                    'pending_payouts': float(stats.pending_payouts),
                    'total_paid_out': float(stats.total_paid_out),
                    'average_rating': float(stats.average_rating),
                    'total_reviews': stats.total_reviews,
                }
            except Exception:
                return None
        return None
    
    def get_buyer_stats(self, obj):
        if obj.role == User.Role.BUYER:
            try:
                profile = obj.buyer_profile
                return {
                    'total_purchases': profile.total_purchases,
                    'total_spent': float(profile.total_spent),
                }
            except Exception:
                return None
        return None


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña."""
    
    old_password = serializers.CharField(required=True, style={'input_type': 'password'})
    new_password = serializers.CharField(
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        style={'input_type': 'password'}
    )
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('La contraseña actual es incorrecta.')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Las contraseñas no coinciden.'
            })
        return attrs


class BankAccountSerializer(serializers.Serializer):
    """Serializer para datos de cuenta bancaria."""
    
    bank_name = serializers.CharField(max_length=100, required=True)
    bank_account_number = serializers.CharField(max_length=50, required=True)
    bank_clabe = serializers.CharField(max_length=20, required=True)
    bank_account_holder = serializers.CharField(max_length=200, required=True)


class SellerOnboardingSerializer(serializers.Serializer):
    """Serializer para registro como vendedor."""
    
    company_name = serializers.CharField(max_length=255, required=False)
    tax_id = serializers.CharField(max_length=50, required=False)
    website = serializers.URLField(required=False)
    bank_name = serializers.CharField(max_length=100, required=True)
    bank_account_number = serializers.CharField(max_length=50, required=True)
    bank_clabe = serializers.CharField(max_length=20, required=True)
    payout_method = serializers.ChoiceField(
        choices=['mercadopago', 'transfer'],
        default='mercadopago'
    )
    
    def validate(self, attrs):
        user = self.context['request'].user
        if user.role == User.Role.SELLER:
            raise serializers.ValidationError('Ya eres vendedor.')
        return attrs
