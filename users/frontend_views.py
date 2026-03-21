"""
Frontend Views para Usuarios
"""

from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, get_user_model
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.contrib import messages
from django.conf import settings

from .forms import UserRegistrationForm

User = get_user_model()


class LoginView(View):
    """Vista de login."""
    template_name = 'account/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None
        
        if user is not None:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            next_url = request.GET.get('next', '/account/dashboard/')
            return redirect(next_url)
        else:
            return render(request, self.template_name, {
                'error': 'Email o contraseña incorrectos'
            })


class RegisterView(View):
    """Vista de registro."""
    template_name = 'account/signup.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('dashboard')
        return render(request, self.template_name)
    
    def post(self, request):
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.email
            user.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('dashboard')
        return render(request, self.template_name, {
            'form': form
        })


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    """Dashboard principal del usuario."""
    template_name = 'account/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['is_admin'] = user.is_admin
        context['is_seller'] = user.is_seller
        context['is_buyer'] = user.is_buyer
        context['page_name'] = 'dashboard'
        
        if user.is_seller:
            try:
                context['seller_stats'] = user.seller_stats
                context['total_earnings'] = float(user.seller_stats.total_earnings or 0)
                context['pending_earnings'] = float(user.seller_stats.available_earnings or 0)
            except Exception:
                context['seller_stats'] = None
                context['total_earnings'] = 0
                context['pending_earnings'] = 0
        
        if user.is_buyer:
            try:
                context['buyer_stats'] = user.buyer_profile
                context['total_purchases'] = user.buyer_profile.total_purchases or 0
            except Exception:
                context['buyer_stats'] = None
                context['total_purchases'] = 0
        
        return context


@method_decorator(login_required, name='dispatch')
class MyProductsView(TemplateView):
    """Mis Productos del vendedor."""
    template_name = 'account/my-products.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['page_name'] = 'my-products'
        context['is_seller'] = user.is_seller
        context['is_admin'] = user.is_admin
        context['is_buyer'] = user.is_buyer
        return context


@method_decorator(login_required, name='dispatch')
class WithdrawView(TemplateView):
    """Retiros de ganancias."""
    template_name = 'account/withdraw.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['page_name'] = 'withdraw'
        context['is_seller'] = user.is_seller
        context['is_admin'] = user.is_admin
        context['is_buyer'] = user.is_buyer
        
        context['available_earnings'] = 0
        context['pending_earnings'] = 0
        context['total_paid_out'] = 0
        context['payouts'] = []
        
        if user.is_seller or user.is_admin:
            try:
                if hasattr(user, 'seller_stats') and user.seller_stats:
                    context['available_earnings'] = float(user.seller_stats.available_earnings or 0)
                    context['pending_earnings'] = float(user.seller_stats.pending_payouts or 0)
                    context['total_paid_out'] = float(user.seller_stats.total_paid_out or 0)
            except Exception:
                pass
            
            try:
                from payments.models import Payout
                context['payouts'] = Payout.objects.filter(seller=user).order_by('-requested_at')[:10]
            except Exception:
                pass
        
        return context
    
    def post(self, request):
        from django.contrib import messages
        messages.success(request, 'Solicitud de retiro enviada correctamente.')
        return self.get(request)


@method_decorator(login_required, name='dispatch')
class PurchasesView(TemplateView):
    """Mis Compras."""
    template_name = 'account/purchases.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = 'purchases'
        context['is_buyer'] = self.request.user.is_buyer
        context['is_seller'] = self.request.user.is_seller
        context['is_admin'] = self.request.user.is_admin
        return context


@method_decorator(login_required, name='dispatch')
class FavoritesView(TemplateView):
    """Mis Favoritos."""
    template_name = 'account/favorites.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = 'favorites'
        context['is_buyer'] = self.request.user.is_buyer
        context['is_seller'] = self.request.user.is_seller
        context['is_admin'] = self.request.user.is_admin
        return context


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    """Perfil del usuario."""
    template_name = 'account/profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_name'] = 'profile'
        context['is_buyer'] = self.request.user.is_buyer
        context['is_seller'] = self.request.user.is_seller
        context['is_admin'] = self.request.user.is_admin
        return context
