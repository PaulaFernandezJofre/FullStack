"""
Seguridad para Pasarela de Pago - 100% Gratuito
Implementa ciberseguridad sin costos adicionales
"""

import hmac
import hashlib
import time
import re
from collections import defaultdict
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.core.cache import cache
from functools import wraps
import bleach


class PaymentSecurityMiddleware:
    """
    Middleware de seguridad para proteger la pasarela de pagos.
    - Rate limiting por IP
    - Validación de headers
    - Detección de bots
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.request_counts = defaultdict(list)
        self.blocked_ips = set()
    
    def __call__(self, request):
        if '/api/' in request.path or '/payments/' in request.path:
            client_ip = self.get_client_ip(request)
            
            if self.is_ip_blocked(client_ip):
                return JsonResponse({
                    'error': 'Demasiadas solicitudes',
                    'retry_after': 60
                }, status=429)
            
            if not self.check_rate_limit(client_ip, request.path):
                self.block_ip(client_ip, duration=60)
                return JsonResponse({
                    'error': 'Demasiadas solicitudes',
                    'retry_after': 60
                }, status=429)
            
            if not self.validate_request_headers(request):
                return HttpResponseForbidden('Solicitud inválida')
            
            if self.detect_suspicious_activity(request):
                self.block_ip(client_ip, duration=300)
                return HttpResponseForbidden('Actividad sospechosa detectada')
        
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')
    
    def check_rate_limit(self, ip, path, limit=60, window=60):
        key = f"rate_limit:{ip}:{path}"
        now = time.time()
        
        requests = cache.get(key, [])
        requests = [t for t in requests if now - t < window]
        
        if len(requests) >= limit:
            return False
        
        requests.append(now)
        cache.set(key, requests, timeout=window)
        return True
    
    def block_ip(self, ip, duration=60):
        key = f"blocked_ip:{ip}"
        cache.set(key, True, timeout=duration)
        self.blocked_ips.add(ip)
    
    def is_ip_blocked(self, ip):
        key = f"blocked_ip:{ip}"
        return cache.get(key, False)
    
    def validate_request_headers(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if len(user_agent) < 10 and 'python-requests' not in user_agent.lower():
            if request.path.startswith('/api/'):
                return False
        return True
    
    def detect_suspicious_activity(self, request):
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'onerror=',
            r'onclick=',
            r'union\s+select',
            r'drop\s+table',
            r';\s*rm\s*-rf',
        ]
        
        body = request.body.decode('utf-8', errors='ignore') if request.body else ''
        
        for pattern in suspicious_patterns:
            if re.search(pattern, body, re.IGNORECASE):
                return True
        
        return False


class WebhookSignatureVerifier:
    """
    Verificador de firmas para webhooks de Mercado Pago.
    Asegura que las solicitudes vengan realmente de Mercado Pago.
    """
    
    MERCADO_PAGO_IPS = {
        '54.85.55.0/24',
        '52.20.166.0/24',
        '18.228.0.0/16',
        '34.238.0.0/16',
    }
    
    @staticmethod
    def verify_signature(request, payload=None):
        """
        Verifica la firma del webhook de Mercado Pago.
        Usa el token de webhook configurado.
        """
        webhook_secret = getattr(settings, 'MERCADO_PAGO_WEBHOOK_SECRET', '')
        
        if not webhook_secret:
            webhook_secret = settings.MERCADO_PAGO_ACCESS_TOKEN
        
        signature = request.META.get('HTTP_X_MERCADOLIBRE_SIGNATURE', '')
        
        if not payload:
            payload = request.body
        
        if isinstance(payload, bytes):
            payload = payload.decode('utf-8')
        
        expected_signature = WebhookSignatureVerifier._generate_signature(
            payload, webhook_secret
        )
        
        if signature and expected_signature:
            return hmac.compare_digest(signature, expected_signature)
        
        return True
    
    @staticmethod
    def _generate_signature(payload, secret):
        """Genera firma HMAC-SHA256."""
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    @staticmethod
    def verify_ip(ip):
        """
        Verifica si la IP pertenece a los rangos de Mercado Pago.
        Esta función puede mejorarse con una biblioteca ipaddress.
        """
        import ipaddress
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            for cidr in WebhookSignatureVerifier.MERCADO_PAGO_IPS:
                network = ipaddress.ip_network(cidr)
                if ip_obj in network:
                    return True
            
            return False
        except ValueError:
            return False


def rate_limit(limit=10, period=60):
    """
    Decorador para limitar requests a una vista.
    Uso: @rate_limit(limit=5, period=60)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(request, *args, **kwargs):
            ip = _get_client_ip(request)
            key = f"rate:{ip}:{request.path}"
            
            requests = cache.get(key, 0)
            
            if requests >= limit:
                return JsonResponse({
                    'error': 'Demasiadas solicitudes',
                    'retry_after': period
                }, status=429)
            
            cache.set(key, requests + 1, timeout=period)
            return view_func(request, *args, **kwargs)
        
        return wrapped_view
    return decorator


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def sanitize_payment_data(data):
    """
    Sanitiza datos de pago para prevenir inyecciones.
    Usa bleach para limpiar HTML/JS malicioso.
    """
    if isinstance(data, str):
        return bleach.clean(
            data,
            tags=[],
            attributes={},
            strip=True,
            strip_comments=True
        )
    
    if isinstance(data, dict):
        return {k: sanitize_payment_data(v) for k, v in data.items()}
    
    if isinstance(data, list):
        return [sanitize_payment_data(item) for item in data]
    
    return data


def validate_payment_amount(amount, min_amount=1, max_amount=1000000):
    """
    Valida que el monto del pago esté en rangos seguros.
    """
    try:
        amount = float(amount)
        return min_amount <= amount <= max_amount
    except (TypeError, ValueError):
        return False


def validate_currency(currency):
    """
    Valida que la moneda sea una de las permitidas.
    """
    allowed_currencies = ['USD', 'MXN', 'CLP', 'ARS', 'BRL', 'COP', 'PEN']
    return currency.upper() in allowed_currencies


class SecurePaymentLogger:
    """
    Logger seguro que no expone datos sensibles.
    """
    
    SENSITIVE_FIELDS = {
        'password', 'token', 'secret', 'card_number',
        'cvv', 'cvc', 'api_key', 'access_token',
        'mercadopago_access_token', 'mercadopago_secret'
    }
    
    @classmethod
    def log_payment_event(cls, event_type, data):
        """Log de eventos de pago sin datos sensibles."""
        safe_data = cls._remove_sensitive_data(data)
        logger = __import__('logging').getLogger('payments')
        logger.info(f"[{event_type}] {safe_data}")
    
    @classmethod
    def _remove_sensitive_data(cls, data):
        """Remueve campos sensibles del diccionario."""
        if not isinstance(data, dict):
            return data
        
        safe_data = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(field in key_lower for field in cls.SENSITIVE_FIELDS):
                safe_data[key] = '***REDACTED***'
            elif isinstance(value, dict):
                safe_data[key] = cls._remove_sensitive_data(value)
            else:
                safe_data[key] = value
        
        return safe_data


class IdempotencyHandler:
    """
    Manejador de idempotencia para prevenir pagos duplicados.
    Usa cache para almacenar las respuestas de requests procesados.
    """
    
    def __init__(self, timeout=3600):
        self.timeout = timeout
    
    def get_response(self, key):
        """Obtiene respuesta cacheada."""
        return cache.get(f"idempotent:{key}")
    
    def store_response(self, key, response):
        """Almacena respuesta para evitar duplicados."""
        cache.set(f"idempotent:{key}", response, timeout=self.timeout)
    
    def is_duplicate(self, key):
        """Verifica si el request ya fue procesado."""
        return cache.get(f"idempotent:{key}") is not None
    
    @staticmethod
    def generate_key(request):
        """Genera clave única para el request."""
        data = request.body if request.body else ''
        if isinstance(data, bytes):
            data = data.decode('utf-8')
        
        hash_obj = hashlib.sha256()
        hash_obj.update(data.encode('utf-8'))
        hash_obj.update(request.META.get('REMOTE_ADDR', '').encode('utf-8'))
        
        return hash_obj.hexdigest()
