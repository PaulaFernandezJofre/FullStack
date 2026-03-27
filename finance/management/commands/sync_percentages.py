"""
Command to sync financial percentages automatically
"""
from django.core.management.base import BaseCommand
from finance.sync import PercentageSyncService, SellerEarningsService
from finance.models import Account


class Command(BaseCommand):
    help = 'Sincroniza automáticamente los porcentajes de comisiones y ganancias'

    def add_arguments(self, parser):
        parser.add_argument(
            '--accounts',
            action='store_true',
            help='Solo sincronizar cuentas',
        )
        parser.add_argument(
            '--sellers',
            action='store_true',
            help='Solo sincronizar vendedores',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Sincronizar todo',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n=== Sincronización de Porcentajes ===\n'))
        
        # Mostrar tasas actuales
        rates = PercentageSyncService.get_current_rates()
        self.stdout.write(f"Tasas del Sistema:")
        self.stdout.write(f"  IVA Chile: {rates['iva']:.1f}%")
        self.stdout.write(f"  Mercado Pago: {rates['mercadopago']:.2f}%")
        self.stdout.write(f"  Plataforma: {rates['platform']:.1f}%")
        self.stdout.write(f"  Vendedor: {rates['seller']:.1f}%\n")
        
        if options.get('accounts') or options.get('all') or not any([options.get('accounts'), options.get('sellers')]):
            self.stdout.write(self.style.WARNING('>> Sincronizando Cuentas...'))
            accounts = PercentageSyncService.update_account_balances()
            for key, account in accounts.items():
                self.stdout.write(
                    f"  {account.name}: ${account.balance:,.0f} ({account.percentage}%)"
                )
            self.stdout.write(self.style.SUCCESS('  [OK] Cuentas actualizadas\n'))
        
        if options.get('sellers') or options.get('all'):
            self.stdout.write(self.style.WARNING('>> Sincronizando Vendedores...'))
            updated = SellerEarningsService.sync_all_sellers()
            for item in updated:
                self.stdout.write(
                    f"  {item['seller']}: ${item['total_earnings']:,.0f}"
                )
            self.stdout.write(self.style.SUCCESS(f'  [OK] {len(updated)} vendedores actualizados\n'))
        
        self.stdout.write(self.style.SUCCESS('=== Sincronización Completa ===\n'))
