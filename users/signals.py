"""
Signals para crear perfiles automáticamente
"""

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import User, SellerStats, BuyerProfile


@receiver(post_save, sender=User)
def create_user_profiles(sender, instance, created, **kwargs):
    """Crea SellerStats y BuyerProfile automáticamente."""
    if created:
        if instance.is_seller:
            SellerStats.objects.get_or_create(user=instance)
        if instance.is_buyer:
            BuyerProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_user_profiles(sender, instance, **kwargs):
    """Guarda los perfiles relacionados."""
    if hasattr(instance, 'seller_stats'):
        instance.seller_stats.save()
    if hasattr(instance, 'buyer_profile'):
        instance.buyer_profile.save()
