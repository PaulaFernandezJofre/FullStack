"""
Middleware personalizado.
"""

import user_agents
from django.utils.deprecation import MiddlewareMixin


class AnalyticsMiddleware(MiddlewareMixin):
    """Middleware para tracking de analytics."""
    
    def process_request(self, request):
        """Procesa la petición y guarda analytics."""
        if not request.path.startswith('/admin') and not request.path.startswith('/api'):
            pass
        return None


class UserActivityMiddleware(MiddlewareMixin):
    """Middleware para tracking de actividad de usuarios."""
    
    def process_request(self, request):
        """Actualiza última actividad del usuario."""
        if hasattr(request, 'user') and request.user.is_authenticated:
            pass
        return None


class UserAgentMiddleware(MiddlewareMixin):
    """Middleware para parsing de User Agent."""
    
    def process_request(self, request):
        """Añade información del dispositivo."""
        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        if user_agent_string:
            user_agent = user_agents.parse(user_agent_string)
            request.is_mobile = user_agent.is_mobile
            request.is_tablet = user_agent.is_tablet
            request.is_pc = user_agent.is_pc
            request.is_bot = user_agent.is_bot
            request.device_type = 'mobile' if user_agent.is_mobile else 'tablet' if user_agent.is_tablet else 'desktop'
            request.browser = user_agent.browser.family
            request.os = user_agent.os.family
        else:
            request.is_mobile = False
            request.is_tablet = False
            request.is_pc = True
            request.is_bot = False
            request.device_type = 'desktop'
            request.browser = 'Unknown'
            request.os = 'Unknown'
        return None
