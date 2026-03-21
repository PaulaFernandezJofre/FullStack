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
            {'question': '¿Cómo funciona LogicPerfect?', 'answer': 'LogicPerfect es un marketplace donde puedes comprar y vender proyectos de programación. Los vendedores publican sus productos y los compradores pueden adquirirlos usando Mercado Pago.'},
            {'question': '¿Cuáles son las comisiones?', 'answer': 'LogicPerfect cobra una comisión del 15% sobre cada venta. El vendedor recibe el 85% restante.'},
            {'question': '¿Cómo recibo mis pagos?', 'answer': 'Los pagos se procesan a través de Mercado Pago. Puedes retirar tus ganancias a tu cuenta una vez que alcances el mínimo de $50 USD.'},
            {'question': '¿Qué tipos de productos puedo vender?', 'answer': 'Puedes vender software, templates, cursos, apps web, apps móviles, plugins, scripts y más.'},
            {'question': '¿Cuánto tiempo tarda en aprobarse un producto?', 'answer': 'Los productos son revisados por nuestro equipo en 24-48 horas hábiles.'},
            {'question': '¿Qué métodos de pago acepta LogicPerfect?', 'answer': 'Aceptamos Mercado Pago como método de pago principal, con soporte para tarjetas de crédito, débito y saldo de Mercado Pago.'},
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
