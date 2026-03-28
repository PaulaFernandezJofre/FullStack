"""
Signals for Orders App
Handles automatic recalculation of order totals when items change
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Order, OrderItem


@receiver(post_save, sender=OrderItem)
def update_order_totals_on_item_save(sender, instance, created, **kwargs):
    """Recalculate order totals when an item is saved."""
    if instance.order and instance.order.status == Order.Status.PENDING:
        instance.order.calculate_totals()
        instance.order.save(update_fields=['subtotal', 'discount', 'total', 
                                          'iva_amount', 'mercadopago_fee',
                                          'platform_maintenance', 'seller_total',
                                          'updated_at'])


@receiver(post_delete, sender=OrderItem)
def update_order_totals_on_item_delete(sender, instance, **kwargs):
    """Recalculate order totals when an item is deleted."""
    try:
        if instance.order and instance.order.status == Order.Status.PENDING:
            instance.order.calculate_totals()
            instance.order.save(update_fields=['subtotal', 'discount', 'total',
                                              'iva_amount', 'mercadopago_fee',
                                              'platform_maintenance', 'seller_total',
                                              'updated_at'])
    except Order.DoesNotExist:
        pass
