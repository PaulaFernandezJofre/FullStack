# DevStack - Marketplace de Proyectos de Programación

**DevStack** es una plataforma de ecommerce profesional para comprar y vender proyectos de programación de alta calidad.

## Características Principales

### Sistema de Usuarios
- **3 roles**: Admin, Vendedor, Comprador
- Autenticación JWT segura
- Perfiles completos de usuario

### Gestión de Productos
- Múltiples tipos: Software, Templates, Cursos, Apps Web/Móviles, Páginas Web
- Categorías jerárquicas
- Sistema de reseñas y calificaciones
- Licencias Regular y Extendida

### Sistema de Pagos
- **Mercado Pago** (única pasarela de pago)
- **85% para vendedores**
- **15% para la plataforma**
- Retiros desde $50 USD

### Dashboard de Analytics
- Ventas y revenue
- Productos más vendidos
- Análisis de usuarios
- Reportes detallados

### Sistema de Tickets
- Soporte al cliente
- Base de conocimiento
- FAQs dinámicos

---

## Requisitos

- Python 3.10+
- PostgreSQL 14+
- Redis (opcional, para cache)
- Cuenta de Mercado Pago (developers.mercadopago.com)

---

## Instalación Paso a Paso

### 1. Clonar y entrar al directorio
```bash
cd C:\Users\pepad\Documents\Ecommerce
```

### 2. Crear entorno virtual
```bash
python -m venv venv
```

### 3. Activar entorno virtual (Windows)
```bash
venv\Scripts\activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Crear archivo .env
```bash
copy .env.example .env
```

Editar `.env` con tus credenciales:
```env
# Django
DJANGO_SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_NAME=devstack_db
DB_USER=postgres
DB_PASSWORD=tu_password
DB_HOST=localhost
DB_PORT=5432

# Mercado Pago (OBLIGATORIO)
MERCADO_PAGO_ACCESS_TOKEN=TEST-xxxxx
MERCADO_PAGO_PUBLIC_KEY=TEST-xxxxx
MERCADO_PAGO_ENVIRONMENT=sandbox

# IVA Chile (Habilitar si vendes a Chile)
MERCADO_PAGO_CHILE_IVA=True
MERCADO_PAGO_CHILE_IVA_RATE=19

# Cloudinary (Gratuito - cloudinary.com)
CLOUDINARY_CLOUD_NAME=tu_cloud_name
CLOUDINARY_API_KEY=tu_api_key
CLOUDINARY_API_SECRET=tu_api_secret

# Site
SITE_URL=http://localhost:8000
```

### 6. Crear base de datos PostgreSQL

Abrir pgAdmin o terminal de PostgreSQL:
```sql
CREATE DATABASE devstack_db;
CREATE USER postgres WITH PASSWORD 'tu_password';
GRANT ALL PRIVILEGES ON DATABASE devstack_db TO postgres;
```

### 7. Ejecutar migraciones
```bash
python manage.py makemigrations
python manage.py migrate
```

### 8. Crear superusuario admin
```bash
python manage.py createsuperuser
```
Sigue las instrucciones para crear usuario admin.

### 9. Recolectar archivos estáticos
```bash
python manage.py collectstatic
```

### 10. Iniciar servidor
```bash
python manage.py runserver
```

### 11. Acceder al proyecto
- **Frontend**: http://localhost:8000/
- **Admin**: http://localhost:8000/admin/
- **API**: http://localhost:8000/api/v1/

---

## Configuración de Mercado Pago (Obligatorio)

### 1. Crear cuenta
1. Ir a https://developers.mercadopago.com
2. Crear cuenta de desarrollador
3. Crear una aplicación

### 2. Obtener credenciales
Del dashboard de Mercado Pago, copiar:
- **Access Token** (para backend)
- **Public Key** (para frontend)

### 3. Configurar Webhook
En el dashboard de Mercado Pago:
1. Ir a Notificaciones > Webhooks
2. Agregar URL: `https://tudominio.com/api/v1/payments/mercadopago/webhook/`
3. Suscribirse a: `payments`, `merchant_orders`

### 4. Modo Sandbox vs Producción
```env
# Sandbox (pruebas)
MERCADO_PAGO_ENVIRONMENT=sandbox

# Producción
MERCADO_PAGO_ENVIRONMENT=production
```

---

## API Endpoints Principales

### Autenticación
- `POST /api/v1/users/auth/login/` - Login
- `POST /api/v1/users/auth/refresh/` - Refresh Token
- `POST /api/v1/users/auth/register/` - Registro

### Usuarios
- `GET /api/v1/users/me/` - Perfil actual
- `PATCH /api/v1/users/me/` - Actualizar perfil
- `POST /api/v1/users/become_seller/` - Convertirse en vendedor

### Productos
- `GET /api/v1/products/` - Listar productos
- `GET /api/v1/products/{slug}/` - Detalle de producto
- `POST /api/v1/products/` - Crear producto (vendedor)
- `GET /api/v1/products/my-products/` - Mis productos

### Carrito y Órdenes
- `POST /api/v1/orders/cart/add/` - Agregar al carrito
- `GET /api/v1/orders/cart/` - Ver carrito
- `POST /api/v1/orders/orders/checkout/` - Finalizar compra
- `GET /api/v1/orders/orders/` - Mis órdenes
- `GET /api/v1/orders/downloads/` - Mis descargas

### Pagos
- `POST /api/v1/payments/mercadopago/create-preference/` - Crear preferencia Mercado Pago
- `GET /api/v1/payments/earnings/` - Mis ganancias
- `POST /api/v1/payments/payouts/request/` - Solicitar retiro
- `GET /api/v1/payments/transactions/` - Transacciones

### Soporte
- `GET /api/v1/support/tickets/` - Mis tickets
- `POST /api/v1/support/tickets/` - Crear ticket
- `GET /api/v1/support/faq/` - FAQs

---

## Estructura del Proyecto

```
devstack/
├── devstack/           # Configuración Django
├── core/               # Funcionalidades core
├── users/              # Modelo de usuario
├── products/           # Catálogo de productos
├── orders/             # Órdenes y carrito
├── payments/           # Sistema de pagos
│   ├── mercadopago_service.py   # Servicio Mercado Pago
│   └── mercadopago_views.py     # Vistas Mercado Pago
├── analytics/          # Dashboard y reportes
├── support/           # Sistema de soporte
├── templates/         # Templates HTML
├── static/            # Archivos estáticos
└── media/             # Archivos subidos
```

---

## Variables de Entorno Importantes

| Variable | Descripción | Default |
|----------|-------------|---------|
| `PAYMENT_GATEWAY` | Pasarela de pago | mercadopago |
| `PLATFORM_COMMISSION_RATE` | Comisión plataforma | 0.15 (15%) |
| `SELLER_COMMISSION_RATE` | Comisión vendedor | 0.85 (85%) |
| `MIN_WITHDRAWAL_AMOUNT` | Mínimo para retiro | $50 USD |
| `MERCADO_PAGO_ENVIRONMENT` | sandbox/production | sandbox |
| `MERCADO_PAGO_CHILE_IVA` | Habilitar IVA Chile (19%) | False |
| `MERCADO_PAGO_CHILE_IVA_RATE` | Tasa IVA Chile | 19 |

---

## Deployment

### Usando Gunicorn (Producción)
```bash
pip install gunicorn
gunicorn devstack.wsgi:application --bind 0.0.0.0:8000
```

### Usando Docker
```bash
docker-compose up -d
```

---

## Testing

```bash
# Ejecutar todos los tests
python manage.py test

# Con coverage
pytest --cov=.
```

---

## Troubleshooting

### Error de migraciones
```bash
python manage.py makemigrations --dry-run
python manage.py makemigrations
python manage.py migrate
```

### Error de credenciales Mercado Pago
Verificar que el Access Token esté correcto y no haya espacios.

### Error de CORS
Agregar el dominio en `CORS_ALLOWED_ORIGINS` en settings.

---

## Licencia

MIT License

## Soporte

- Email: soporte@devstack.com
- Crear ticket: /api/v1/support/tickets/
