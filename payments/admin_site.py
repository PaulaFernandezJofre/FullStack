"""
Dashboard de Mercado Pago para Admin
Muestra el estado de la conexión y configuración
"""

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.template.response import TemplateResponse
from django.urls import path
from django.conf import settings


class MercadoPagoAdminSite(AdminSite):
    """
    Admin site personalizado con sección de Mercado Pago
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.final_catch_all_view = False
    
    def get_urls(self):
        urls = super().get_urls()
        urls += [
            path('mercadopago/', self.admin_view(self.mercadopago_dashboard), name='mercadopago_dashboard'),
        ]
        return urls
    
    def mercadopago_dashboard(self, request):
        """
        Dashboard de Mercado Pago con estado de conexión
        """
        mp_config = {
            'access_token': bool(settings.MERCADO_PAGO_ACCESS_TOKEN),
            'access_token_masked': self._mask_token(settings.MERCADO_PAGO_ACCESS_TOKEN) if settings.MERCADO_PAGO_ACCESS_TOKEN else None,
            'public_key': bool(settings.MERCADO_PAGO_PUBLIC_KEY),
            'public_key_masked': self._mask_key(settings.MERCADO_PAGO_PUBLIC_KEY) if settings.MERCADO_PAGO_PUBLIC_KEY else None,
            'environment': settings.MERCADO_PAGO_ENVIRONMENT,
            'is_sandbox': settings.MERCADO_PAGO_ENVIRONMENT == 'sandbox',
            'chile_iva_enabled': settings.MERCADO_PAGO_CHILE_IVA,
            'chile_iva_rate': settings.MERCADO_PAGO_CHILE_IVA_RATE,
        }
        
        distribution = {
            'iva_rate': settings.IVA_RATE * 100,
            'mercadopago_fee_rate': settings.MERCADO_PAGO_FEE_RATE * 100,
            'platform_rate': settings.PLATFORM_MAINTENANCE_RATE * 100,
            'seller_rate': settings.SELLER_RATE * 100,
        }
        
        context = {
            **self.each_context(request),
            'title': 'Mercado Pago',
            'mp_config': mp_config,
            'distribution': distribution,
        }
        return TemplateResponse(request, 'admin/mercadopago_dashboard.html', context)
    
    def _mask_token(self, token):
        """Enmascara el token de acceso"""
        if len(token) > 10:
            return f"{token[:8]}...{token[-4:]}"
        return "***"
    
    def _mask_key(self, key):
        """Enmascara la clave pública"""
        if len(key) > 10:
            return f"{key[:8]}...{key[-4:]}"
        return "***"


mercadopago_admin_site = MercadoPagoAdminSite(name='mercadopago_admin')


class MercadoPagoConfigModelAdmin:
    """
    Mixin para agregar información de Mercado Pago a cualquier admin
    """
    
    def mercadopago_status(self, obj):
        return 'Configurado' if settings.MERCADO_PAGO_ACCESS_TOKEN else 'No configurado'
    mercadopago_status.short_description = 'MP'
    
    def get_mp_actions(self, obj):
        return ['sync_mercadopago']
