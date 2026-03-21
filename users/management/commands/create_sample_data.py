from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from products.models import Category, Tag, Product
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Creates sample data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample data...')

        # Create test users
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@logicperfect.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS('Created admin user: admin / admin123'))

        seller_user, created = User.objects.get_or_create(
            username='seller',
            defaults={
                'email': 'seller@logicperfect.com',
                'first_name': 'Carlos',
                'last_name': 'Developer',
                'role': 'seller',
            }
        )
        if created:
            seller_user.set_password('seller123')
            seller_user.save()
            self.stdout.write(self.style.SUCCESS('Created seller user: seller / seller123'))

        buyer_user, created = User.objects.get_or_create(
            username='buyer',
            defaults={
                'email': 'buyer@example.com',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'role': 'buyer',
            }
        )
        if created:
            buyer_user.set_password('buyer123')
            buyer_user.save()
            self.stdout.write(self.style.SUCCESS('Created buyer user: buyer / buyer123'))

        # Create categories
        categories_data = [
            {'name': 'Software', 'slug': 'software', 'description': 'Aplicaciones de software y herramientas'},
            {'name': 'Templates', 'slug': 'templates', 'description': 'Plantillas web y UI kits'},
            {'name': 'Cursos', 'slug': 'cursos', 'description': 'Cursos de programación y tecnología'},
            {'name': 'Plugins', 'slug': 'plugins', 'description': 'Plugins y extensiones'},
            {'name': 'Scripts', 'slug': 'scripts', 'description': 'Scripts y automatización'},
            {'name': 'Apps Móviles', 'slug': 'apps-moviles', 'description': 'Aplicaciones móviles'},
        ]

        categories = {}
        for cat_data in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            categories[cat_data['slug']] = cat
            if created:
                self.stdout.write(f'Created category: {cat.name}')

        # Create tags
        tags_data = ['python', 'javascript', 'react', 'django', 'nodejs', 'flutter', 'vue', 'angular', 'api', 'dashboard']
        tags = {}
        for tag_name in tags_data:
            tag, created = Tag.objects.get_or_create(
                name=tag_name,
                slug=tag_name
            )
            tags[tag_name] = tag

        # Create sample products
        products_data = [
            {
                'name': 'Dashboard Admin React',
                'slug': 'dashboard-admin-react',
                'category': categories['templates'],
                'seller': seller_user,
                'price': Decimal('49.99'),
                'short_description': 'Dashboard administrativo completo con React y Tailwind CSS',
                'description': 'Dashboard administrativo moderno con más de 50 componentes, gráficos, tablas y más.',
                'product_type': 'template',
                'tags': [tags['react'], tags['dashboard'], tags['javascript']],
            },
            {
                'name': 'Sistema de Gestión de Tareas',
                'slug': 'sistema-gestion-tareas',
                'category': categories['software'],
                'seller': seller_user,
                'price': Decimal('79.99'),
                'short_description': 'Sistema completo de gestión de tareas con Django',
                'description': 'Aplicación web completa para gestión de tareas con Kanban, usuarios y reportes.',
                'product_type': 'software',
                'tags': [tags['django'], tags['python'], tags['dashboard']],
            },
            {
                'name': 'Curso de Python para Principiantes',
                'slug': 'curso-python-principiantes',
                'category': categories['cursos'],
                'seller': seller_user,
                'price': Decimal('29.99'),
                'short_description': 'Aprende Python desde cero con proyectos prácticos',
                'description': 'Curso completo de Python con más de 30 lecciones y 10 proyectos prácticos.',
                'product_type': 'course',
                'tags': [tags['python']],
            },
            {
                'name': 'Plugin WordPress de Membresías',
                'slug': 'plugin-wordpress-membresias',
                'category': categories['plugins'],
                'seller': seller_user,
                'price': Decimal('39.99'),
                'short_description': 'Plugin completo de membresías para WordPress',
                'description': 'Crea planes de suscripción y membresías en tu sitio WordPress.',
                'product_type': 'plugin',
                'tags': [tags['api']],
            },
            {
                'name': 'Script de Automatización Python',
                'slug': 'script-automatizacion-python',
                'category': categories['scripts'],
                'seller': seller_user,
                'price': Decimal('19.99'),
                'short_description': 'Script para automatizar tareas repetitivas',
                'description': 'Colección de scripts Python para automatizar tareas del día a día.',
                'product_type': 'script',
                'tags': [tags['python'], tags['api']],
            },
            {
                'name': 'App Móvil de Fitness',
                'slug': 'app-movil-fitness',
                'category': categories['apps-moviles'],
                'seller': seller_user,
                'price': Decimal('59.99'),
                'short_description': 'Aplicación móvil completa con Flutter',
                'description': 'App de seguimiento de ejercicios y nutrición con Flutter y Firebase.',
                'product_type': 'app',
                'tags': [tags['flutter']],
            },
        ]

        for prod_data in products_data:
            tags_list = prod_data.pop('tags')
            product, created = Product.objects.get_or_create(
                slug=prod_data['slug'],
                defaults={
                    **prod_data,
                    'status': 'approved',
                    'regular_license_price': prod_data['price'],
                }
            )
            if created:
                product.tags.set(tags_list)
                self.stdout.write(self.style.SUCCESS(f'Created product: {product.name}'))

        self.stdout.write(self.style.SUCCESS('\nSample data created successfully!'))
        self.stdout.write('\nTest accounts:')
        self.stdout.write('  Admin: admin / admin123')
        self.stdout.write('  Seller: seller / seller123')
        self.stdout.write('  Buyer: buyer / buyer123')
