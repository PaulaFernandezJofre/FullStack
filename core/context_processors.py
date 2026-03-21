"""
Context processors para templates.
"""

from django.conf import settings


def cart_context(request):
    """Añade el carrito al contexto de las plantillas."""
    context = {
        'cart_item_count': 0,
        'cart_total': 0,
    }
    
    if request.user.is_authenticated:
        try:
            cart = request.user.cart.first()
            if cart:
                context['cart_item_count'] = cart.items_count
                context['cart_total'] = float(cart.total)
        except Exception:
            pass
    else:
        session_key = request.session.session_key
        if session_key:
            try:
                from orders.models import Cart
                cart = Cart.objects.filter(session_key=session_key).first()
                if cart:
                    context['cart_item_count'] = cart.items_count
                    context['cart_total'] = float(cart.total)
            except Exception:
                pass
    
    return context


def site_settings(request):
    """Añade la configuración del sitio al contexto."""
    return {
        'site_name': getattr(settings, 'SITE_NAME', 'LogicPerfect'),
        'site_tagline': getattr(settings, 'SITE_TAGLINE', ''),
        'site_description': getattr(settings, 'SITE_DESCRIPTION', ''),
        'site_url': getattr(settings, 'SITE_URL', ''),
        'support_email': getattr(settings, 'SUPPORT_EMAIL', ''),
    }


def social_auth_settings(request):
    """Añade la configuración de autenticación social al contexto."""
    return {
        'social_auth_available': getattr(settings, 'SOCIAL_AUTH_AVAILABLE', False),
    }
