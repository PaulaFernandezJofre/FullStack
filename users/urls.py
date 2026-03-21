"""
URLs de Usuario
"""

from django.urls import path, include
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter

from .views import UserViewSet, LogoutView, CustomTokenObtainPairView
from .frontend_views import (
    LoginView, RegisterView, DashboardView, ProfileView,
    MyProductsView, WithdrawView, PurchasesView, FavoritesView
)
from rest_framework_simplejwt.views import TokenRefreshView

router = DefaultRouter()
router.register('', UserViewSet, basename='users')

urlpatterns = [
    # Frontend - Auth
    path('login/', LoginView.as_view(), name='login'),
    path('register/', RegisterView.as_view(), name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='/'), name='logout'),
    
    # Frontend - Dashboard Pages (cada una con su propia vista)
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('my-products/', MyProductsView.as_view(), name='my-products'),
    path('withdraw/', WithdrawView.as_view(), name='withdraw'),
    path('purchases/', PurchasesView.as_view(), name='purchases'),
    path('favorites/', FavoritesView.as_view(), name='favorites'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # API
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/logout/', LogoutView.as_view(), name='api-logout'),
    path('api/', include(router.urls)),
]
