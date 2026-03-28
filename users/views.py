"""
Vistas de Usuario
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from django.contrib.auth import get_user_model

from .models import UserSession, SellerStats
from .serializers import (
    UserSerializer, UserRegistrationSerializer, UserProfileSerializer,
    PasswordChangeSerializer, SellerOnboardingSerializer, UserPublicSerializer
)

User = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet para usuarios."""
    
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'id'
    
    def get_permissions(self):
        if self.action == 'create':
            return [permissions.AllowAny()]
        elif self.action in ['retrieve', 'me', 'update_profile']:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAdminUser()]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'retrieve' and self.kwargs.get('id') != 'me':
            return UserPublicSerializer
        elif self.action == 'me':
            return UserProfileSerializer
        return UserSerializer
    
    def get_object(self):
        if self.kwargs.get('id') == 'me':
            return self.request.user
        return super().get_object()
    
    @action(detail=False, methods=['get', 'patch'])
    def me(self, request):
        """Obtiene o actualiza el perfil del usuario actual."""
        if request.method == 'GET':
            serializer = UserProfileSerializer(request.user)
            return Response(serializer.data)
        
        serializer = UserProfileSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Cambia la contraseña del usuario."""
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({'message': 'Contraseña actualizada correctamente.'})
    
    @action(detail=False, methods=['post'])
    def become_seller(self, request):
        """Convierte al usuario en vendedor."""
        serializer = SellerOnboardingSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.role = User.Role.SELLER
        user.company_name = serializer.validated_data.get('company_name', '')
        user.tax_id = serializer.validated_data.get('tax_id', '')
        user.website = serializer.validated_data.get('website', '')
        user.payout_method = serializer.validated_data.get('payout_method', 'transfer')
        user.bank_name = serializer.validated_data.get('bank_name', '')
        user.bank_account_number = serializer.validated_data.get('bank_account_number', '')
        user.bank_clabe = serializer.validated_data.get('bank_clabe', '')
        user.save()
        
        SellerStats.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Ahora eres vendedor.',
            'user': UserProfileSerializer(user).data
        })
    
    @action(detail=False, methods=['get'])
    def sellers(self, request):
        """Lista de vendedores."""
        sellers = User.objects.filter(
            role__in=[User.Role.SELLER, User.Role.ADMIN],
            status=User.Status.ACTIVE
        )
        
        page = self.paginate_queryset(sellers)
        if page is not None:
            serializer = UserPublicSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = UserPublicSerializer(sellers, many=True)
        return Response(serializer.data)


class LogoutView(APIView):
    """Cierra sesión del usuario."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Sesión cerrada correctamente.'})
        except Exception:
            return Response(
                {'error': 'Error al cerrar sesión.'},
                status=status.HTTP_400_BAD_REQUEST
            )


class UserSessionViewSet(viewsets.ReadOnlyModelViewSet):
    """Gestión de sesiones del usuario."""
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserSession.objects.filter(user=self.request.user)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Serializer personalizado que incluye datos del usuario."""
    
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['email'] = user.email
        token['role'] = user.role
        token['username'] = user.username
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        data['user'] = {
            'id': str(self.user.id),
            'email': self.user.email,
            'username': self.user.username,
            'role': self.user.role,
            'first_name': self.user.first_name,
            'last_name': self.user.last_name,
        }
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """Vista personalizada para obtener token con datos de usuario."""
    serializer_class = CustomTokenObtainPairSerializer
