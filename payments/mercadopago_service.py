"""
Mercado Pago Service
Integración con la pasarela de pago de Mercado Libre
"""

import mercadopago
from django.conf import settings
from django.urls import reverse
import logging

logger = logging.getLogger(__name__)


class MercadoPagoService:
    """Servicio para interactuar con la API de Mercado Pago."""
    
    def __init__(self):
        self.access_token = settings.MERCADO_PAGO_ACCESS_TOKEN
        self.public_key = settings.MERCADO_PAGO_PUBLIC_KEY
        self.environment = settings.MERCADO_PAGO_ENVIRONMENT
        
        self.sdk = mercadopago.SDK(self.access_token)
    
    def create_preference(self, items, payer=None, order=None, back_urls=None):
        """
        Crea una preferencia de pago en Mercado Pago.
        
        Args:
            items: Lista de items a comprar
            payer: Información del comprador
            order: Orden de compra
            back_urls: URLs de retorno
            
        Returns:
            dict con preference_id e init_point
        """
        preference_data = {
            "items": items,
            "payer": payer or {},
            "external_reference": str(order.id) if order else None,
            "notification_url": settings.SITE_URL + reverse('payments:mercadopago-webhook'),
            "statement_descriptor": "DEVSTACK",
            "binary_mode": False,
        }
        
        if getattr(settings, 'MERCADO_PAGO_CHILE_IVA', False):
            preference_data["taxes"] = [
                {
                    "type": "VAT",
                    "value": settings.MERCADO_PAGO_CHILE_IVA_RATE
                }
            ]
        
        if back_urls:
            preference_data["back_urls"] = {
                "success": back_urls.get('success', settings.SITE_URL),
                "pending": back_urls.get('pending', settings.SITE_URL),
                "failure": back_urls.get('failure', settings.SITE_URL),
            }
        
        try:
            result = self.sdk.preference().create(preference_data)
            
            if result["status"] == 201:
                preference = result["response"]
                return {
                    "success": True,
                    "preference_id": preference["id"],
                    "init_point": preference.get("init_point"),
                    "sandbox_init_point": preference.get("sandbox_init_point"),
                }
            else:
                logger.error(f"Mercado Pago error: {result}")
                return {
                    "success": False,
                    "error": result.get("response", {}).get("message", "Error desconocido")
                }
        except Exception as e:
            logger.error(f"Exception creating preference: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_payment(self, payment_id):
        """
        Obtiene información de un pago específico.
        
        Args:
            payment_id: ID del pago en Mercado Pago
            
        Returns:
            dict con información del pago
        """
        try:
            result = self.sdk.payment().get(payment_id)
            
            if result["status"] == 200:
                return {
                    "success": True,
                    "payment": result["response"]
                }
            return {
                "success": False,
                "error": "Payment not found"
            }
        except Exception as e:
            logger.error(f"Error getting payment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_payment_by_external_ref(self, external_reference):
        """
        Obtiene pagos por referencia externa.
        
        Args:
            external_reference: Referencia externa (ID de orden)
            
        Returns:
            Lista de pagos
        """
        try:
            result = self.sdk.payment().search({
                "external_reference": external_reference
            })
            
            if result["status"] == 200:
                return {
                    "success": True,
                    "payments": result["response"]["results"]
                }
            return {
                "success": False,
                "error": "Search failed"
            }
        except Exception as e:
            logger.error(f"Error searching payments: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def refund_payment(self, payment_id, amount=None):
        """
        Reembolsa un pago.
        
        Args:
            payment_id: ID del pago
            amount: Monto a reembolsar (opcional, si no se especifica se reembolsa todo)
            
        Returns:
            dict con resultado del reembolso
        """
        try:
            refund_data = {}
            if amount:
                refund_data["amount"] = float(amount)
            
            result = self.sdk.refund().create(payment_id, refund_data)
            
            if result["status"] in [200, 201]:
                return {
                    "success": True,
                    "refund": result["response"]
                }
            return {
                "success": False,
                "error": result.get("response", {}).get("message", "Refund failed")
            }
        except Exception as e:
            logger.error(f"Error refunding payment: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def cancel_preapproval(self, preapproval_id):
        """
        Cancela una suscripción.
        
        Args:
            preapproval_id: ID de la aprobación de suscripción
            
        Returns:
            dict con resultado
        """
        try:
            result = self.sdk.preapproval().update(preapproval_id, {
                "status": "cancelled"
            })
            
            if result["status"] == 200:
                return {
                    "success": True
                }
            return {
                "success": False,
                "error": "Cancellation failed"
            }
        except Exception as e:
            logger.error(f"Error cancelling preapproval: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_merchant_orders(self, merchant_order_id):
        """
        Obtiene una orden de comerciante.
        
        Args:
            merchant_order_id: ID de la orden
            
        Returns:
            dict con información de la orden
        """
        try:
            result = self.sdk.merchant_order().get(merchant_order_id)
            
            if result["status"] == 200:
                return {
                    "success": True,
                    "order": result["response"]
                }
            return {
                "success": False,
                "error": "Order not found"
            }
        except Exception as e:
            logger.error(f"Error getting merchant order: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def map_payment_status(status):
        """
        Mapea el estado de Mercado Pago al estado interno.
        
        Args:
            status: Estado de Mercado Pago
            
        Returns:
            Estado mapeado
        """
        status_mapping = {
            "approved": "completed",
            "pending": "pending",
            "in_process": "processing",
            "rejected": "failed",
            "cancelled": "cancelled",
            "refunded": "refunded",
            "partially_refunded": "partially_refunded",
        }
        return status_mapping.get(status, "pending")
    
    def get_preference_by_id(self, preference_id):
        """
        Obtiene una preferencia por su ID.
        
        Args:
            preference_id: ID de la preferencia
            
        Returns:
            dict con información de la preferencia
        """
        try:
            result = self.sdk.preference().get(preference_id)
            
            if result["status"] == 200:
                return {
                    "success": True,
                    "preference": result["response"]
                }
            return {
                "success": False,
                "error": "Preference not found"
            }
        except Exception as e:
            logger.error(f"Error getting preference: {e}")
            return {
                "success": False,
                "error": str(e)
            }
