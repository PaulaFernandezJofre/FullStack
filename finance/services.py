"""
Servicios Financieros
Lógica de distribución de pagos y cálculos financieros
"""

from decimal import Decimal
from django.db.models import Sum

from .models import Account, PaymentDistribution, FinancialTransaction, AccountType, TransactionType, TransactionStatus


class PaymentDistributionService:
    """Servicio para distribuir pagos entre cuentas."""
    
    @staticmethod
    def distribute_payment(order, order_item=None):
        """
        Distribuye el pago de una orden entre las cuentas.
        
        Para $100.000 CLP:
        - IVA (19%): ~$16.000 → Cuenta IVA
        - Mercado Pago (~6%): ~$5.040 → Cuenta MP
        - Plataforma (15%): $15.000 → Cuenta Platform
        - Vendedor (~64%): ~$63.960 → Cuenta Seller
        """
        # Obtener monto bruto
        if order_item:
            gross_amount = order_item.price
            category = order_item.product.category if hasattr(order_item, 'product') else None
        else:
            gross_amount = order.total_amount
            category = None
        
        # Calcular distribución
        distribution_data = PaymentDistribution.calculate_distribution(gross_amount)
        
        # Crear distribución
        distribution = PaymentDistribution.objects.create(
            order=order,
            order_item=order_item,
            gross_amount=distribution_data['gross_amount'],
            iva_amount=distribution_data['iva_amount'],
            mercadopago_fee=distribution_data['mercadopago_fee'],
            platform_fee=distribution_data['platform_fee'],
            seller_amount=distribution_data['seller_amount'],
            category=category,
            status=TransactionStatus.COMPLETED,
        )
        
        # Actualizar cuentas
        PaymentDistributionService._update_accounts(distribution)
        
        # Registrar transacciones financieras
        PaymentDistributionService._create_transactions(distribution, order)
        
        # Actualizar resumen por categoría
        if category:
            PaymentDistributionService._update_category_summary(category, distribution)
        
        return distribution
    
    @staticmethod
    def _update_accounts(distribution):
        """Actualiza los balances de las cuentas."""
        # IVA Chile
        iva_account, _ = Account.objects.get_or_create(
            account_type=AccountType.IVA,
            defaults={'name': 'IVA Chile (19%)', 'percentage': Decimal('19.00')}
        )
        iva_account.total_credits += distribution.iva_amount
        iva_account.save()
        
        # Mercado Pago
        mp_account, _ = Account.objects.get_or_create(
            account_type=AccountType.MERCADO_PAGO,
            defaults={'name': 'Comisión Mercado Pago', 'percentage': Decimal('5.99')}
        )
        mp_account.total_credits += distribution.mercadopago_fee
        mp_account.save()
        
        # Plataforma
        platform_account, _ = Account.objects.get_or_create(
            account_type=AccountType.PLATFORM_MAINTENANCE,
            defaults={'name': 'Ganancia Plataforma (15%)', 'percentage': Decimal('15.00')}
        )
        platform_account.total_credits += distribution.platform_fee
        platform_account.save()
        
        # Vendedor
        seller_account, _ = Account.objects.get_or_create(
            account_type=AccountType.SELLER_EARNINGS,
            defaults={'name': 'Ganancias Vendedores', 'percentage': Decimal('64.00')}
        )
        seller_account.total_credits += distribution.seller_amount
        seller_account.save()
    
    @staticmethod
    def _create_transactions(distribution, order):
        """Crea transacciones financieras para la distribución."""
        # IVA
        iva_account = Account.objects.get(account_type=AccountType.IVA)
        FinancialTransaction.objects.create(
            transaction_type=TransactionType.IVA_CHARGE,
            account=iva_account,
            amount=distribution.iva_amount,
            distribution=distribution,
            order=order,
            description=f'IVA Chile (19%) - Orden {order.order_number}',
            status=TransactionStatus.COMPLETED,
        )
        
        # Mercado Pago
        mp_account = Account.objects.get(account_type=AccountType.MERCADO_PAGO)
        FinancialTransaction.objects.create(
            transaction_type=TransactionType.MERCADO_PAGO_FEE,
            account=mp_account,
            amount=distribution.mercadopago_fee,
            distribution=distribution,
            order=order,
            description=f'Comisión Mercado Pago - Orden {order.order_number}',
            status=TransactionStatus.COMPLETED,
        )
        
        # Plataforma
        platform_account = Account.objects.get(account_type=AccountType.PLATFORM_MAINTENANCE)
        FinancialTransaction.objects.create(
            transaction_type=TransactionType.PLATFORM_FEE,
            account=platform_account,
            amount=distribution.platform_fee,
            distribution=distribution,
            order=order,
            description=f'Ganancia Plataforma (15%) - Orden {order.order_number}',
            status=TransactionStatus.COMPLETED,
        )
        
        # Vendedor
        seller_account = Account.objects.get(account_type=AccountType.SELLER_EARNINGS)
        FinancialTransaction.objects.create(
            transaction_type=TransactionType.SALE,
            account=seller_account,
            user=order.user,
            amount=distribution.seller_amount,
            distribution=distribution,
            order=order,
            description=f'Pago a vendedor - Orden {order.order_number}',
            status=TransactionStatus.COMPLETED,
        )
    
    @staticmethod
    def _update_category_summary(category, distribution):
        """Actualiza el resumen financiero por categoría."""
        from finance.models import CategoryFinancialSummary
        
        summary, _ = CategoryFinancialSummary.objects.get_or_create(category=category)
        
        summary.total_sales += 1
        summary.total_revenue += distribution.gross_amount
        summary.total_iva += distribution.iva_amount
        summary.total_mercadopago_fees += distribution.mercadopago_fee
        summary.total_platform_fees += distribution.platform_fee
        summary.total_seller_payouts += distribution.seller_amount
        summary.save()


class FinancialReportService:
    """Servicio para generar reportes financieros."""
    
    @staticmethod
    def get_account_balances():
        """Obtiene los balances de todas las cuentas."""
        accounts = Account.objects.all()
        total = sum(a.balance for a in accounts)
        
        return {
            'accounts': [
                {
                    'name': a.name,
                    'type': a.account_type,
                    'balance': a.balance,
                    'percentage': a.percentage,
                }
                for a in accounts
            ],
            'total': total,
        }
    
    @staticmethod
    def get_distribution_summary():
        """Resumen de distribuciones por estado."""
        from finance.models import TransactionStatus
        
        return {
            'total_distributions': PaymentDistribution.objects.count(),
            'completed': PaymentDistribution.objects.filter(status=TransactionStatus.COMPLETED).count(),
            'pending': PaymentDistribution.objects.filter(status=TransactionStatus.PENDING).count(),
            'total_revenue': PaymentDistribution.objects.filter(
                status=TransactionStatus.COMPLETED
            ).aggregate(Sum('gross_amount'))['gross_amount__sum'] or Decimal('0'),
            'total_iva': PaymentDistribution.objects.filter(
                status=TransactionStatus.COMPLETED
            ).aggregate(Sum('iva_amount'))['iva_amount__sum'] or Decimal('0'),
            'total_platform': PaymentDistribution.objects.filter(
                status=TransactionStatus.COMPLETED
            ).aggregate(Sum('platform_fee'))['platform_fee__sum'] or Decimal('0'),
            'total_seller': PaymentDistribution.objects.filter(
                status=TransactionStatus.COMPLETED
            ).aggregate(Sum('seller_amount'))['seller_amount__sum'] or Decimal('0'),
        }
    
    @staticmethod
    def get_category_breakdown():
        """Desglose por categoría."""
        from finance.models import CategoryFinancialSummary
        from products.models import Category
        
        categories = Category.objects.all()
        breakdown = []
        
        for cat in categories:
            summary = CategoryFinancialSummary.objects.filter(category=cat).first()
            if summary:
                breakdown.append({
                    'name': cat.name,
                    'slug': cat.slug,
                    'sales': summary.total_sales,
                    'revenue': summary.total_revenue,
                    'iva': summary.total_iva,
                    'mp_fee': summary.total_mercadopago_fees,
                    'platform': summary.total_platform_fees,
                    'seller': summary.total_seller_payouts,
                })
            else:
                breakdown.append({
                    'name': cat.name,
                    'slug': cat.slug,
                    'sales': 0,
                    'revenue': Decimal('0'),
                    'iva': Decimal('0'),
                    'mp_fee': Decimal('0'),
                    'platform': Decimal('0'),
                    'seller': Decimal('0'),
                })
        
        return breakdown
