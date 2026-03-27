"""
Servicios de Sincronización de Porcentajes
Mantiene actualizados los porcentajes de comisiones y ganancias
"""

from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from .models import Account, PaymentDistribution, FinancialTransaction, AccountType, TransactionType, TransactionStatus


class PercentageSyncService:
    """
    Servicio para sincronizar y calcular automáticamente los porcentajes
    de distribución de ganancias.
    """
    
    # Tasas fijas del sistema (no modificables por usuario)
    IVA_RATE = Decimal('0.19')  # 19%
    MP_FEE_RATE = Decimal('0.0599')  # ~6%
    PLATFORM_RATE = Decimal('0.15')  # 15%
    SELLER_RATE = Decimal('0.64')  # ~64%
    
    @classmethod
    def get_current_rates(cls):
        """Retorna las tasas actuales del sistema."""
        return {
            'iva': float(cls.IVA_RATE * 100),
            'mercadopago': float(cls.MP_FEE_RATE * 100),
            'platform': float(cls.PLATFORM_RATE * 100),
            'seller': float(cls.SELLER_RATE * 100),
        }
    
    @classmethod
    def calculate_distribution(cls, gross_amount):
        """
        Calcula la distribución exacta basada en las tasas del sistema.
        Para $100.000 CLP:
        - IVA (19%): ~$15.966
        - Mercado Pago (~6%): ~$5.034
        - Plataforma (15%): $15.000
        - Vendedor (~64%): $64.000
        """
        gross = Decimal(str(gross_amount))
        
        # IVA Chile (19%)
        iva = gross * cls.IVA_RATE / (Decimal('1') + cls.IVA_RATE)
        
        # Monto sin IVA
        amount_without_iva = gross - iva
        
        # Mercado Pago (~6% sobre monto sin IVA)
        mercadopago = amount_without_iva * cls.MP_FEE_RATE
        
        # Después de costos
        after_costs = amount_without_iva - mercadopago
        
        # Plataforma (15%)
        platform_profit = gross * cls.PLATFORM_RATE
        
        # Vendedor (el resto = ~64%)
        seller = after_costs - platform_profit
        
        return {
            'gross_amount': gross,
            'iva_amount': iva.quantize(Decimal('1')),
            'mercadopago_fee': mercadopago.quantize(Decimal('1')),
            'platform_fee': platform_profit.quantize(Decimal('1')),
            'seller_amount': seller.quantize(Decimal('1')),
            'iva_rate': cls.IVA_RATE * 100,
            'mp_rate': cls.MP_FEE_RATE * 100,
            'platform_rate': cls.PLATFORM_RATE * 100,
            'seller_rate': (seller / gross * 100).quantize(Decimal('0.01')) if gross > 0 else Decimal('0'),
        }
    
    @classmethod
    def update_account_balances(cls):
        """
        Actualiza los balances de todas las cuentas basado en las transacciones.
        """
        # Obtener resumen de todas las distribuciones completadas
        distributions = PaymentDistribution.objects.filter(
            status=TransactionStatus.COMPLETED
        )
        
        totals = distributions.aggregate(
            total_iva=Sum('iva_amount'),
            total_mp=Sum('mercadopago_fee'),
            total_platform=Sum('platform_fee'),
            total_seller=Sum('seller_amount'),
        )
        
        # Actualizar cuenta IVA
        iva_account, _ = Account.objects.get_or_create(
            account_type=AccountType.IVA,
            defaults={'name': 'IVA Chile (19%)', 'percentage': cls.IVA_RATE * 100}
        )
        iva_account.total_credits = totals['total_iva'] or Decimal('0')
        iva_account.percentage = cls.IVA_RATE * 100
        iva_account.save()
        
        # Actualizar cuenta Mercado Pago
        mp_account, _ = Account.objects.get_or_create(
            account_type=AccountType.MERCADO_PAGO,
            defaults={'name': 'Comisión Mercado Pago', 'percentage': cls.MP_FEE_RATE * 100}
        )
        mp_account.total_credits = totals['total_mp'] or Decimal('0')
        mp_account.percentage = cls.MP_FEE_RATE * 100
        mp_account.save()
        
        # Actualizar cuenta Plataforma
        platform_account, _ = Account.objects.get_or_create(
            account_type=AccountType.PLATFORM_MAINTENANCE,
            defaults={'name': 'Ganancia Plataforma (15%)', 'percentage': cls.PLATFORM_RATE * 100}
        )
        platform_account.total_credits = totals['total_platform'] or Decimal('0')
        platform_account.percentage = cls.PLATFORM_RATE * 100
        platform_account.save()
        
        # Actualizar cuenta Vendedores
        seller_account, _ = Account.objects.get_or_create(
            account_type=AccountType.SELLER_EARNINGS,
            defaults={'name': 'Ganancias Vendedores', 'percentage': cls.SELLER_RATE * 100}
        )
        seller_account.total_credits = totals['total_seller'] or Decimal('0')
        seller_account.percentage = cls.SELLER_RATE * 100
        seller_account.save()
        
        return {
            'iva': iva_account,
            'mercadopago': mp_account,
            'platform': platform_account,
            'seller': seller_account,
        }
    
    @classmethod
    def get_financial_summary(cls):
        """
        Obtiene un resumen financiero completo con los porcentajes calculados.
        """
        accounts = Account.objects.all()
        total = sum(a.balance for a in accounts)
        
        account_data = []
        for a in accounts:
            rate = float(a.percentage) if a.percentage else 0
            account_data.append({
                'name': a.name,
                'type': a.account_type,
                'balance': float(a.balance),
                'percentage': rate,
                'formatted_balance': f"${a.balance:,.0f}",
                'formatted_percentage': f"{rate:.1f}%",
            })
        
        return {
            'accounts': account_data,
            'total': float(total),
            'rates': cls.get_current_rates(),
            'last_updated': timezone.now(),
        }
    
    @classmethod
    def get_category_breakdown(cls):
        """
        Obtiene el desglose financiero por categoría.
        """
        from products.models import Category
        
        categories = Category.objects.all()
        breakdown = []
        
        for cat in categories:
            distributions = PaymentDistribution.objects.filter(
                category=cat,
                status=TransactionStatus.COMPLETED
            )
            
            totals = distributions.aggregate(
                total_sales=Sum('gross_amount'),
                total_iva=Sum('iva_amount'),
                total_mp=Sum('mercadopago_fee'),
                total_platform=Sum('platform_fee'),
                total_seller=Sum('seller_amount'),
            )
            
            if totals['total_sales']:
                breakdown.append({
                    'name': cat.name,
                    'slug': cat.slug,
                    'sales_count': distributions.count(),
                    'revenue': float(totals['total_sales'] or 0),
                    'iva': float(totals['total_iva'] or 0),
                    'mercadopago': float(totals['total_mp'] or 0),
                    'platform': float(totals['total_platform'] or 0),
                    'seller': float(totals['total_seller'] or 0),
                })
        
        return breakdown


class SellerEarningsService:
    """
    Servicio para calcular y actualizar las ganancias de cada vendedor.
    """
    
    @classmethod
    def calculate_seller_earnings(cls, seller):
        """
        Calcula las ganancias de un vendedor específico.
        """
        from orders.models import OrderItem
        from users.models import SellerStats
        
        # Obtener todas las ventas del vendedor
        sales = PaymentDistribution.objects.filter(
            order__items__product__seller=seller,
            status=TransactionStatus.COMPLETED
        ).values(
            'seller_amount'
        ).aggregate(
            total_earnings=Sum('seller_amount'),
            total_sales=Sum('gross_amount'),
            total_iva=Sum('iva_amount'),
            total_mp=Sum('mercadopago_fee'),
            total_platform=Sum('platform_fee'),
        )
        
        return {
            'seller': seller,
            'total_earnings': sales['total_earnings'] or Decimal('0'),
            'total_sales': sales['total_sales'] or Decimal('0'),
            'total_iva': sales['total_iva'] or Decimal('0'),
            'total_mercadopago': sales['total_mp'] or Decimal('0'),
            'total_platform': sales['total_platform'] or Decimal('0'),
            'seller_rate': PercentageSyncService.SELLER_RATE * 100,
        }
    
    @classmethod
    def update_seller_stats(cls, seller):
        """
        Actualiza las estadísticas del vendedor.
        """
        from users.models import SellerStats
        from products.models import Product
        
        earnings = cls.calculate_seller_earnings(seller)
        
        stats, _ = SellerStats.objects.get_or_create(user=seller)
        
        stats.total_earnings = earnings['total_earnings']
        stats.total_revenue = earnings['total_sales']
        stats.total_platform_commission = earnings['total_platform']
        
        # Contar productos activos
        stats.total_products = Product.objects.filter(seller=seller).count()
        stats.active_products = Product.objects.filter(seller=seller, is_active=True).count()
        
        stats.save()
        
        return stats
    
    @classmethod
    def sync_all_sellers(cls):
        """
        Sincroniza las estadísticas de todos los vendedores.
        """
        from users.models import User
        
        sellers = User.objects.filter(role__in=['seller', 'admin'])
        updated = []
        
        for seller in sellers:
            stats = cls.update_seller_stats(seller)
            updated.append({
                'seller': seller.email,
                'total_earnings': float(stats.total_earnings),
            })
        
        return updated
