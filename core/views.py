"""
Vistas Core
"""

from django.shortcuts import render
from django.views.generic import TemplateView


def handler_404(request, exception):
    return render(request, 'errors/404.html', status=404)


def handler_500(request):
    return render(request, 'errors/500.html', status=500)


def handler_403(request, exception):
    return render(request, 'errors/403.html', status=403)


def handler_400(request, exception):
    return render(request, 'errors/400.html', status=400)


class HelpCenterView(TemplateView):
    """Centro de Ayuda."""
    template_name = 'pages/help.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Centro de Ayuda'
        return context


class ContactView(TemplateView):
    """Página de Contacto."""
    template_name = 'pages/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Contacto'
        return context
    
    def post(self, request):
        from django.contrib import messages
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        messages.success(request, '¡Gracias por contactarnos! Te responderemos pronto.')
        return render(request, self.template_name, {'page_title': 'Contacto'})


class FAQView(TemplateView):
    """Página de Preguntas Frecuentes."""
    template_name = 'pages/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'FAQ'
        context['faqs'] = [
            {'question': '¿Cómo funciona LogicPerfect?', 
             'answer': 'Marketplace para comprar y vender proyectos de programación.'},
            {'question': '¿Cuáles son las comisiones?', 
             'answer': 'El vendedor recibe el 64%. El resto va a plataforma, IVA y Mercado Pago.'},
            {'question': '¿Cómo recibo mis pagos?', 
             'answer': 'Los pagos se procesan con Mercado Pago. Mínimo de retiro: $50 USD.'},
            {'question': '¿Qué productos puedo vender?', 
             'answer': 'Software, templates, cursos, apps, plugins, scripts y más.'},
            {'question': '¿Cuánto tiempo tarda en aprobarse un producto?', 
             'answer': 'Los productos son revisados por nuestro equipo en 24-48 horas hábiles.'},
            {'question': '¿Qué métodos de pago acepta LogicPerfect?', 
             'answer': 'Aceptamos Mercado Pago con soporte para tarjetas de crédito, débito y saldo.'},
        ]
        return context


class TermsView(TemplateView):
    """Términos y Condiciones."""
    template_name = 'pages/terms.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Términos y Condiciones'
        return context


class PrivacyView(TemplateView):
    """Política de Privacidad."""
    template_name = 'pages/privacy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Política de Privacidad'
        return context


class LicensesView(TemplateView):
    """Página de Licencias."""
    template_name = 'pages/licenses.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Licencias'
        return context


class SellerGuideView(TemplateView):
    """Guía del Vendedor."""
    template_name = 'pages/seller_guide.html'


class BuyerGuideView(TemplateView):
    """Guía del Comprador."""
    template_name = 'pages/buyer_guide.html'


class PaymentsGuideView(TemplateView):
    """Guía de Pagos y Retiros."""
    template_name = 'pages/payments_guide.html'


class AccountGuideView(TemplateView):
    """Guía de Cuenta y Seguridad."""
    template_name = 'pages/account_guide.html'
