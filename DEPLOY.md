# 🚀 Guía de Despliegue - LogicPerfect

## Gratis para Siempre: Render.com

Esta guía te permite desplegar LogicPerfect en **Render.com** con:
- ✅ Hosting web gratuito (750 horas/mes)
- ✅ PostgreSQL gratuito (1 base de datos)
- ✅ SSL automático
- ✅ Dominio gratuito `.onrender.com`
- ✅ CDN y CDN para archivos estáticos

---

## 📋 Requisitos Previos

1. **Cuenta en GitHub** - https://github.com
2. **Cuenta en Render.com** - https://render.com (gratis)
3. **Tu código en GitHub**

---

## 🚀 Paso 1: Subir tu código a GitHub

```bash
# En tu carpeta del proyecto
git init
git add .
git commit -m "Initial commit - LogicPerfect"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/logicperfect.git
git push -u origin main
```

---

## 🚀 Paso 2: Crear cuenta en Render.com

1. Ve a https://render.com
2. Click en **"Sign Up"**
3. Usa tu cuenta de **GitHub**
4. Autoriza el acceso a tus repositorios

---

## 🚀 Paso 3: Crear Base de Datos PostgreSQL

1. En Render Dashboard, click **"New +"**
2. Selecciona **"PostgreSQL"**
3. Configura:
   - **Name**: `logicperfect-db`
   - **Database**: `logicperfect`
   - **Plan**: **Free**
4. Click **"Create Database"**
5. **Guarda la Connection String** (la necesitarás después)

---

## 🚀 Paso 4: Desplegar la Aplicación Web

### Opción A: Blueprint (Automático)

1. En Render, click **"New +"** → **"Blueprint"**
2. Sube el archivo `render.yaml` de este proyecto
3. Conecta tu repositorio de GitHub
4. Render detectará automáticamente:
   - Web Service
   - PostgreSQL Database
5. Click **"Apply"**

### Opción B: Manual

1. Click **"New +"** → **"Web Service"**
2. Configura:
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Start Command**: `gunicorn devstack.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4`
3. Click **"Create Web Service"**

---

## 🚀 Paso 5: Configurar Variables de Entorno

En tu Web Service de Render, ve a **"Environment"** y agrega:

### Variables Obligatorias:

| Variable | Valor |
|----------|-------|
| `PYTHON_VERSION` | `3.12` |
| `DJANGO_SECRET_KEY` | `[Genera una clave segura]` |
| `DEBUG` | `False` |
| `ALLOWED_HOSTS` | `logicperfect.onrender.com` |
| `DATABASE_URL` | `[Connection string de PostgreSQL]` |

### Para generar DJANGO_SECRET_KEY:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Variables Opcionales:

| Variable | Valor |
|----------|-------|
| `MERCADO_PAGO_ACCESS_TOKEN` | Tu token de Mercado Pago |
| `MERCADO_PAGO_PUBLIC_KEY` | Tu public key |
| `SENDGRID_API_KEY` | Tu API key de SendGrid |

---

## 🚀 Paso 6: Configurar Mercado Pago (Opcional)

1. Crea cuenta en https://www.mercadopago.com/developers
2. Obtén tus credenciales del Dashboard
3. Agrega las variables en Render:
   - `MERCADO_PAGO_ACCESS_TOKEN`
   - `MERCADO_PAGO_PUBLIC_KEY`
   - `MERCADO_PAGO_ENVIRONMENT=sandbox` (o `production`)

---

## 🚀 Paso 7: Crear Superusuario

Después del despliegue, crea tu usuario administrador:

1. Ve a tu Web Service en Render
2. Click en **"Shell"** para abrir terminal
3. Ejecuta:
```bash
python manage.py createsuperuser
```
4. Ingresa email y contraseña

---

## 🚀 Paso 8: Poblar con Datos de Prueba

```bash
python manage.py create_sample_data
```

Esto creará:
- 3 usuarios (admin, seller, buyer)
- 6 categorías
- 6 productos de ejemplo

---

## 🌐 Acceso a tu Aplicación

- **URL**: `https://logicperfect.onrender.com` (o tu dominio personalizado)
- **Admin**: `https://logicperfect.onrender.com/admin/`
- **API**: `https://logicperfect.onrender.com/api/`

---

## 🔧 Configurar Dominio Personalizado (Opcional)

### Usando .tk, .ml, .ga, .cf, .gq (Gratuitos)

1. Ve a https://www.freenom.com
2. Busca un dominio gratuito
3. Selecciona **Register** por 12 meses
4. En **Management Tools → Nameservers**:
   - Selecciona **Use custom nameservers**
   - Agrega los nameservers de Cloudflare:
     - `ns1.cloudflare.com`
     - `ns2.cloudflare.com`

### Conectar en Cloudflare (Gratis)

1. Crea cuenta en https://dash.cloudflare.com
2. Agrega tu dominio gratuito
3. Configura DNS pointing a tu URL de Render
4. Activa **SSL/TLS** → **Full**

### En Render

1. Ve a tu Web Service → **Settings**
2. Busca **Custom Domains**
3. Agrega tu dominio personalizado

---

## 📊 Recursos Gratuitos

| Servicio | Recursos | Enlace |
|----------|----------|--------|
| **Render** | 750h/mes web + PostgreSQL | render.com |
| **Cloudflare** | DNS + SSL + CDN | cloudflare.com |
| **Freenom** | Dominios .tk/.ml/.ga | freenom.com |
| **SendGrid** | 100 emails/día | sendgrid.com |
| **Mercado Pago** | Pagos (sin costo mensual) | mercadopago.com |

---

## ⚠️ Notas Importantes

### Free Tier de Render
- El servicio **duerme después de 15 minutos** de inactividad
- Se **reactiva automáticamente** cuando alguien lo访问a
- Primer deploy puede tardar **2-3 minutos**
- Database free tier tiene **1GB** máximo

### Optimización
- Usa ** whitenoise** para archivos estáticos (incluido)
- Imágenes se almacenan en la DB (para proyectos pequeños)
- Para proyectos grandes, considera **Cloudinary** (gratuito)

---

## 🆘 Solución de Problemas

### Error 500 en producción
```bash
# Revisa los logs en Render Dashboard → Logs
# Ejecuta en shell:
python manage.py check --deploy
```

### Error de migraciones
```bash
python manage.py migrate --run-syncdb
```

### Static files no cargan
```bash
python manage.py collectstatic --noinput
```

### Memory error
- Upgrade a **Starter** plan ($7/mes) si es necesario

---

## ✅ Checklist Final

- [ ] Código en GitHub
- [ ] Cuenta en Render creada
- [ ] PostgreSQL creado
- [ ] Web Service desplegado
- [ ] Variables de entorno configuradas
- [ ] Migraciones ejecutadas
- [ ] Superusuario creado
- [ ] SSL activo (automático)
- [ ] Aplicación funcionando

---

## 🎉 ¡Listo!

Tu aplicación está ahora en vivo en:
```
https://logicperfect.onrender.com
```

**Costo total: $0/mes** (mientras uses el free tier)
