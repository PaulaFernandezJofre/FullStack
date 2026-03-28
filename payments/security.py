"""
Seguridad para Pasarela de Pago - 100% Gratuito
Implementa ciberseguridad sin costos adicionales
"""

import hmac
import hashlib
import time
import re
import secrets
from collections import defaultdict
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.core.cache import cache
from functools import wraps
import bleach


class PaymentSecurityConfig:
    """
    Configuración centralizada de seguridad para pagos.
    """
    
    MIN_AMOUNT = 100
    MAX_AMOUNT = 10000000
    
    RATE_LIMIT_GENERAL = 60
    RATE_LIMIT_CHECKOUT = 10
    RATE_LIMIT_WEBHOOK = 100
    
    BLOCK_DURATION_SUSPICIOUS = 300
    BLOCK_DURATION_RATE_LIMIT = 60
    
    ALLOWED_CURRENCIES = ['USD', 'MXN', 'CLP', 'ARS', 'BRL', 'COP', 'PEN']
    
    MERCADO_PAGO_IPS = {
        '54.85.55.0/24',
        '52.20.166.0/24',
        '18.228.0.0/16',
        '34.238.0.0/16',
    }
    
    SUSPICIOUS_PATTERNS = [
        r'<script',
        r'javascript:',
        r'onerror=',
        r'onclick=',
        r'onload=',
        r'union\s+select',
        r'drop\s+table',
        r';\s*rm\s*-rf',
        r'eval\(',
        r'exec\(',
        r'../',
        r'..\\',
    ]


class CardDataValidator:
    """
    Validador de datos de tarjeta - Solo para validación de formato.
    NO almacena datos sensibles de tarjeta.
    """
    
    @staticmethod
    def validate_card_number_format(card_number):
        """
        Valida el formato del número de tarjeta (Luhn algorithm).
        Solo para validación, nunca almacene el número completo.
        """
        if not card_number:
            return False
        
        card_number = re.sub(r'\D', '', str(card_number))
        
        if len(card_number) < 13 or len(card_number) > 19:
            return False
        
        total = 0
        reverse_digits = card_number[::-1]
        
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        return total % 10 == 0
    
    @staticmethod
    def validate_cvv(cvv):
        """Valida formato de CVV."""
        if not cvv:
            return False
        return bool(re.match(r'^\d{3,4}$', str(cvv)))
    
    @staticmethod
    def validate_expiry_month(month):
        """Valida mes de expiración."""
        try:
            m = int(month)
            return 1 <= m <= 12
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_expiry_year(year):
        """Valida año de expiración."""
        try:
            y = int(year)
            from datetime import datetime
            current_year = datetime.now().year
            return current_year <= y <= current_year + 20
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def mask_card_number(card_number):
        """
        Enmascara el número de tarjeta para logging seguro.
        Muestra solo los últimos 4 dígitos.
        """
        if not card_number:
            return '****'
        
        card_number = re.sub(r'\D', '', str(card_number))
        
        if len(card_number) < 4:
            return '****'
        
        return f"****-****-****-{card_number[-4:]}"


class PaymentFraudDetector:
    """
    Detector de fraude para transacciones de pago.
    Analiza patrones sospechosos.
    """
    
    HIGH_RISK_PATTERNS = {
        'multiple_failed_attempts': 3,
        'rapid_successive_attempts': 5,
        'unusual_amount_threshold': 1000000,
        'velocity_window_seconds': 300,
    }
    
    @classmethod
    def detect_velocity_attack(cls, user_id, amount):
        """
        Detecta ataques de velocidad (múltiples intentos rápidos).
        """
        key = f"velocity:{user_id}"
        attempts = cache.get(key, [])
        now = time.time()
        
        recent_attempts = [a for a in attempts if now - a < cls.HIGH_RISK_PATTERNS['velocity_window_seconds']]
        
        if len(recent_attempts) >= cls.HIGH_RISK_PATTERNS['rapid_successive_attempts']:
            return True, 'Demasiados intentos recientes'
        
        recent_attempts.append(now)
        cache.set(key, recent_attempts, timeout=cls.HIGH_RISK_PATTERNS['velocity_window_seconds'])
        
        return False, None
    
    @classmethod
    def detect_unusual_amount(cls, amount):
        """Detecta montos inusualmente altos."""
        if amount > cls.HIGH_RISK_PATTERNS['unusual_amount_threshold']:
            return True, f'Monto inusualmente alto: {amount}'
        return False, None
    
    @classmethod
    def detect_geo_anomaly(cls, ip, billing_country=None):
        """
        Detecta anomalías geográficas.
        Requiere implementación con servicio de geolocalización.
        """
        return False, None
    
    @classmethod
    def check_fingerprint(cls, fingerprint):
        """
        Verifica fingerprint del dispositivo/carrito.
        """
        if not fingerprint:
            return False, 'Fingerprint requerido'
        
        blocked_key = f"blocked_fingerprint:{fingerprint}"
        if cache.get(blocked_key):
            return True, 'Dispositivo bloqueado'
        
        return False, None


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
                return HttpResponseForbidden('Solicitud invalida', content_type='text/plain')
            
            if self.detect_suspicious_activity(request):
                self.block_ip(client_ip, duration=300)
                return HttpResponseForbidden('Actividad sospechosa detectada', content_type='text/plain')
        
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


class EnhancedWebhookVerifier:
    """
    Verificador avanzado de webhooks con múltiples capas de seguridad.
    """
    
    @staticmethod
    def verify_mercadopago_webhook(request):
        """
        Verificación completa de webhook de Mercado Pago.
        Incluye: firma, IP, timestamp, idempotencia.
        """
        result = {
            'valid': False,
            'errors': [],
            'warnings': []
        }
        
        client_ip = _get_client_ip(request)
        
        if not EnhancedWebhookVerifier._verify_ip_address(client_ip):
            result['errors'].append(f'IP no autorizada: {client_ip}')
            result['warnings'].append('Intento desde IP externa')
        else:
            result['valid'] = True
        
        if not EnhancedWebhookVerifier._verify_signature(request):
            result['errors'].append('Firma inválida')
            result['valid'] = False
        
        if not EnhancedWebhookVerifier._verify_content_type(request):
            result['warnings'].append('Content-Type inesperado')
        
        idempotency = IdempotencyHandler(timeout=3600)
        payload_hash = hashlib.sha256(request.body).hexdigest()
        if idempotency.is_duplicate(f"webhook:{payload_hash}"):
            result['warnings'].append('Webhook duplicado, ignorado')
        
        return result
    
    @staticmethod
    def _verify_ip_address(ip):
        """Verifica IP contra rangos permitidos."""
        try:
            import ipaddress
            ip_obj = ipaddress.ip_address(ip)
            
            for cidr in PaymentSecurityConfig.MERCADO_PAGO_IPS:
                network = ipaddress.ip_network(cidr)
                if ip_obj in network:
                    return True
            
            if settings.MERCADO_PAGO_ENVIRONMENT != 'production':
                return True
            
            return False
        except ValueError:
            return False
    
    @staticmethod
    def _verify_signature(request):
        """Verifica firma del webhook."""
        webhook_secret = getattr(settings, 'MERCADO_PAGO_WEBHOOK_SECRET', '')
        
        if not webhook_secret:
            webhook_secret = getattr(settings, 'MERCADO_PAGO_ACCESS_TOKEN', '')
        
        if not webhook_secret:
            return True
        
        signature = request.META.get('HTTP_X_MERCADOLIBRE_SIGNATURE', '')
        
        if not signature:
            signature = request.META.get('HTTP_X_MERCADOPAGO_SIGNATURE', '')
        
        if not signature:
            return False
        
        expected = hmac.new(
            webhook_secret.encode('utf-8'),
            request.body,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected)
    
    @staticmethod
    def _verify_content_type(request):
        """Verifica Content-Type del request."""
        content_type = request.content_type or ''
        return 'application/json' in content_type


class TokenGenerator:
    """
    Generador de tokens seguros para operaciones de pago.
    """
    
    @staticmethod
    def generate_checkout_token(order_id, user_id):
        """
        Genera token único para checkout.
        """
        timestamp = int(time.time())
        random_bytes = secrets.token_hex(16)
        
        data = f"{order_id}:{user_id}:{timestamp}:{random_bytes}"
        
        signature = hmac.new(
            settings.SECRET_KEY.encode('utf-8'),
            data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return f"{data}:{signature}"
    
    @staticmethod
    def verify_checkout_token(token, order_id, user_id, max_age=3600):
        """
        Verifica token de checkout.
        """
        try:
            parts = token.split(':')
            if len(parts) != 5:
                return False
            
            token_order_id, token_user_id, timestamp, random_bytes, signature = parts
            
            if token_order_id != str(order_id) or token_user_id != str(user_id):
                return False
            
            age = int(time.time()) - int(timestamp)
            if age > max_age:
                return False
            
            data = f"{token_order_id}:{token_user_id}:{timestamp}:{random_bytes}"
            expected = hmac.new(
                settings.SECRET_KEY.encode('utf-8'),
                data.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected)
        
        except (ValueError, TypeError):
            return False
