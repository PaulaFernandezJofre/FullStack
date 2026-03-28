"""
Vistas de Pagos con Mercado Pago - Versión Segura
Incluye validación, rate limiting y protección contra ataques
"""

from decimal import Decimal
from django.conf import settings
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.contrib import messages
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from orders.models import Order
from .models import Transaction, SellerEarning, PlatformRevenue
from .mercadopago_service import MercadoPagoService
from .security import (
    WebhookSignatureVerifier,
    EnhancedWebhookVerifier,
    sanitize_payment_data,
    validate_payment_amount,
    SecurePaymentLogger,
    IdempotencyHandler,
    PaymentSecurityConfig,
    CardDataValidator,
    PaymentFraudDetector
)
import logging
import json
import re

logger = logging.getLogger(__name__)


class SecureCheckoutThrottle(UserRateThrottle):
    """Limitador de requests para checkout."""
    rate = '10/minute'


class MercadoPagoCheckoutView(APIView):
    """Crea la preferencia de pago con validaciones de seguridad."""
    
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [SecureCheckoutThrottle]
    
    def post(self, request):
        order_id = request.data.get('order_id')
        
        if not order_id:
            return Response(
                {'error': 'Se requiere order_id'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not self._validate_uuid(order_id):
            return Response(
                {'error': 'ID de orden inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            order = Order.objects.get(id=order_id, buyer=request.user)
        except (Order.DoesNotExist, ValueError):
            return Response(
                {'error': 'Orden no encontrada'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if order.status != 'pending':
            return Response(
                {'error': 'Esta orden ya fue procesada'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not validate_payment_amount(float(order.total)):
            return Response(
                {'error': 'Monto de orden inválido'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        items = []
        for item in order.items.select_related('product').all():
            if not validate_payment_amount(float(item.price)):
                continue
            
            items.append({
                "id": str(item.id)[:50],
                "title": sanitize_payment_data(item.product.name)[:100],
                "quantity": min(item.quantity, 100),
                "currency_id": sanitize_payment_data(order.currency),
                "unit_price": round(float(item.price), 2)
            })
        
        if not items:
            return Response(
                {'error': 'No hay items válidos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payer = {
            "name": sanitize_payment_data(request.user.first_name or '')[:50],
            "surname": sanitize_payment_data(request.user.last_name or '')[:50],
            "email": sanitize_payment_data(request.user.email)[:100],
        }
        
        site_url = settings.SITE_URL.rstrip('/')
        
        if not site_url.startswith(('http://', 'https://')):
            site_url = 'https://' + site_url
        
        back_urls = {
            "success": f"{site_url}/orders/{order.id}/success/",
            "pending": f"{site_url}/orders/{order.id}/pending/",
            "failure": f"{site_url}/orders/{order.id}/failed/",
        }
        
        mp_service = MercadoPagoService()
        result = mp_service.create_preference(
            items=items,
            payer=payer,
            order=order,
            back_urls=back_urls
        )
        
        if result['success']:
            order.mercadopago_preference_id = result['preference_id']
            order.save(update_fields=['mercadopago_preference_id', 'updated_at'])
            
            Transaction.objects.create(
                user=request.user,
                order=order,
                transaction_type='sale',
                amount=order.total,
                currency=order.currency,
                mercadopago_preference_id=result['preference_id'],
                status='pending'
            )
            
            SecurePaymentLogger.log_payment_event('checkout_created', {
                'order_id': str(order.id),
                'preference_id': result['preference_id'],
                'total': float(order.total)
            })
            
            init_point = result.get('sandbox_init_point') if mp_service.environment == 'sandbox' \
                else result.get('init_point')
            
            return Response({
                'success': True,
                'preference_id': result['preference_id'],
                'init_point': init_point,
            })
        else:
            SecurePaymentLogger.log_payment_event('checkout_failed', {
                'order_id': str(order.id),
                'error': result.get('error')
            })
            return Response(
                {'error': result.get('error', 'Error al crear preferencia')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @staticmethod
    def _validate_uuid(value):
        uuid_pattern = re.compile(
            r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
            re.IGNORECASE
        )
        return bool(uuid_pattern.match(str(value)))


@csrf_exempt
@require_POST
def mercadopago_webhook(request):
    """
    Webhook seguro de Mercado Pago.
    Valida firma, IP y previene ataques.
    """
    try:
        client_ip = _get_client_ip(request)
        
        payload = request.body
        data = json.loads(payload)
        
        SecurePaymentLogger.log_payment_event('webhook_received', {
            'ip': client_ip,
            'topic': data.get('topic', data.get('type'))
        })
        
        verification = EnhancedWebhookVerifier.verify_mercadopago_webhook(request)
        
        if verification['errors']:
            logger.warning(f"Webhook rejected - errors: {verification['errors']} from IP: {client_ip}")
            return HttpResponseForbidden('Solicitud rechazada')
        
        if verification['warnings']:
            logger.warning(f"Webhook warnings: {verification['warnings']} from IP: {client_ip}")
        
        topic = data.get('topic') or data.get('type')
        
        if not topic:
            return HttpResponse(status=200)
        
        if topic == 'payment':
            payment_id = data.get('resource')
            if payment_id and _is_safe_payment_id(payment_id):
                return process_payment_notification(payment_id)
        
        elif topic == 'merchant_order':
            merchant_order_id = data.get('resource')
            if merchant_order_id and _is_safe_id(merchant_order_id):
                return process_merchant_order_notification(merchant_order_id)
        
        return HttpResponse(status=200)
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return HttpResponse(status=400)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return HttpResponse(status=500)


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def _verify_webhook_authenticity(request, payload):
    verifier = WebhookSignatureVerifier()
    
    if settings.MERCADO_PAGO_ENVIRONMENT == 'production':
        if not verifier.verify_ip(_get_client_ip(request)):
            return False
    
    return verifier.verify_signature(request, payload)


def _is_safe_payment_id(value):
    return bool(re.match(r'^\d{1,20}$', str(value)))


def _is_safe_id(value):
    return bool(re.match(r'^\d{1,20}$', str(value)))


def process_payment_notification(payment_id):
    """Procesa notificación de pago de forma segura."""
    try:
        mp_service = MercadoPagoService()
        result = mp_service.get_payment(payment_id)
        
        if not result['success']:
            return HttpResponse(status=200)
        
        payment = result['payment']
        external_ref = payment.get('external_reference')
        payment_status = payment.get('status')
        
        if not external_ref:
            return HttpResponse(status=200)
        
        try:
            order = Order.objects.get(id=external_ref)
        except (Order.DoesNotExist, ValueError):
            return HttpResponse(status=200)
        
        mapped_status = MercadoPagoService.map_payment_status(payment_status)
        
        if mapped_status == 'completed' and order.status == 'pending':
            process_successful_payment(order, payment)
        
        elif mapped_status in ('failed', 'cancelled'):
            order.status = mapped_status
            order.save(update_fields=['status', 'updated_at'])
        
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error processing payment notification: {e}")
        return HttpResponse(status=500)


def process_merchant_order_notification(merchant_order_id):
    """Procesa notificación de orden de forma segura."""
    try:
        idempotency = IdempotencyHandler()
        cache_key = f"merchant_order:{merchant_order_id}"
        
        if idempotency.is_duplicate(cache_key):
            return HttpResponse(status=200)
        
        mp_service = MercadoPagoService()
        result = mp_service.get_merchant_orders(merchant_order_id)
        
        if not result['success']:
            return HttpResponse(status=200)
        
        order_data = result['order']
        payments = order_data.get('payments', [])
        
        for payment_data in payments:
            if payment_data.get('status') == 'approved':
                external_ref = order_data.get('external_reference')
                if external_ref:
                    try:
                        order = Order.objects.get(id=external_ref)
                        if order.status == 'pending':
                            process_successful_payment(order, payment_data)
                    except (Order.DoesNotExist, ValueError):
                        pass
        
        idempotency.store_response(cache_key, {'processed': True})
        return HttpResponse(status=200)
    
    except Exception as e:
        logger.error(f"Error processing merchant order: {e}")
        return HttpResponse(status=500)


def process_successful_payment(order, payment_data):
    """Procesa pago exitoso con validaciones."""
    try:
        idempotency = IdempotencyHandler()
        cache_key = f"order_completed:{order.id}"
        
        if idempotency.is_duplicate(cache_key):
            return
        
        order.status = 'completed'
        order.mercadopago_payment_id = str(payment_data.get('id', ''))[:100]
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'mercadopago_payment_id', 'paid_at', 'updated_at'])
        
        for item in order.items.select_related('product', 'product__seller').all():
            seller = item.product.seller
            gross_amount = item.unit_price * item.quantity
            
            commission_rate = Decimal(str(settings.PLATFORM_COMMISSION_RATE))
            commission_amount = gross_amount * commission_rate
            net_amount = gross_amount - commission_amount
            
            SellerEarning.objects.create(
                seller=seller,
                order=order,
                order_item=item,
                source='sale',
                gross_amount=gross_amount,
                commission_rate=commission_rate,
                commission_amount=commission_amount,
                net_amount=net_amount,
                currency=order.currency
            )
            
            seller.seller_stats.total_earnings += net_amount
            seller.seller_stats.available_earnings += net_amount
            seller.seller_stats.total_sales += 1
            seller.seller_stats.save(update_fields=['total_earnings', 'available_earnings', 'total_sales'])
            
            item.product.total_sales += 1
            item.product.save(update_fields=['total_sales'])
        
        PlatformRevenue.objects.create(
            source='sale',
            order=order,
            gross_amount=order.subtotal,
            net_amount=order.subtotal * Decimal(str(settings.PLATFORM_COMMISSION_RATE))
        )
        
        transaction = order.transactions.first()
        if transaction:
            transaction.status = 'completed'
            transaction.mercadopago_payment_id = str(payment_data.get('id', ''))
            transaction.completed_at = timezone.now()
            transaction.save(update_fields=['status', 'mercadopago_payment_id', 'completed_at'])
        
        idempotency.store_response(cache_key, {'completed': True})
        
        SecurePaymentLogger.log_payment_event('payment_completed', {
            'order_id': str(order.id),
            'payment_id': str(payment_data.get('id', '')),
            'total': float(order.total)
        })
    
    except Exception as e:
        logger.error(f"Error processing successful payment: {e}")


class MercadoPagoSuccessView(APIView):
    """Página de éxito después del pago."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, order_id):
        try:
            if not MercadoPagoCheckoutView._validate_uuid(order_id):
                messages.error(request, 'Orden no válida')
                return redirect('home')
            
            order = Order.objects.get(id=order_id)
            
            if order.status == 'completed':
                messages.success(request, '¡Pago completado exitosamente!')
            elif order.status == 'pending':
                messages.info(request, 'Tu pago está siendo procesado.')
            
            context = {
                'order': order,
                'payment_status': order.status
            }
            return render(request, 'payments/success.html', context)
        
        except (Order.DoesNotExist, ValueError):
            messages.error(request, 'Orden no encontrada')
            return redirect('home')


class MercadoPagoRefundView(APIView):
    """Vista para procesar reembolsos."""
    
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, order_id):
        reason = request.data.get('reason', 'Reembolso solicitado')
        
        try:
            order = Order.objects.get(id=order_id, status='completed')
        except Order.DoesNotExist:
            return Response(
                {'error': 'Orden no encontrada o no reembolsable'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not order.mercadopago_payment_id:
            return Response(
                {'error': 'No hay ID de pago de Mercado Pago'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            mp_service = MercadoPagoService()
            result = mp_service.refund_payment(
                order.mercadopago_payment_id,
                amount=float(order.total)
            )
            
            if result['success']:
                order.status = 'refunded'
                order.save(update_fields=['status', 'updated_at'])
                
                SecurePaymentLogger.log_payment_event('refund_processed', {
                    'order_id': str(order.id),
                    'amount': float(order.total)
                })
                
                return Response({
                    'success': True,
                    'message': 'Reembolso procesado exitosamente'
                })
            else:
                return Response(
                    {'error': result.get('error', 'Error al procesar reembolso')},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Error processing refund: {e}")
            return Response(
                {'error': 'Error al procesar reembolso'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
