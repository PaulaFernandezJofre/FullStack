# Northflank Deployment Guide - LogicPerfect
# ==========================================

## 1. Crear Base de Datos en Neon

1. Ve a https://neon.tech
2. Regístrate con GitHub
3. Click **"New Project"**
4. Configura:
   - Project name: `logicperfect-db`
   - Region: `US East` (o la más cercana)
   - Compute size: `Free`
5. Click **"Create Project"**
6. En **"Connection Details"**, copia la **Connection String**:
   ```
   postgres://usuario:password@ep-xxx-123456.us-east-2.aws.neon.tech/logicperfect
   ```

---

## 2. Desplegar en Northflank

1. Ve a https://northflank.com
2. Regístrate con GitHub
3. Click **"New Service"** → **"Build from Git"**
4. Conecta tu repo: `PaulaFernandezJofre/FullStack`
5. Configura:
   - **Build Pack**: Python
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate`
   - **Run Command**: `gunicorn devstack.wsgi:application --bind 0.0.0.0:$PORT`
   - **Port**: `8000`

---

## 3. Configurar Variables de Entorno

En tu servicio Northflank, ve a **"Environment"** y agrega:

| Variable | Valor |
|----------|-------|
| `PYTHON_VERSION` | `3.12` |
| `DEBUG` | `False` |
| `DJANGO_SECRET_KEY` | `sk-prod-abc123xyz789def456ghi789jkl012mno345pqr678stu901vwx` |
| `ALLOWED_HOSTS` | `tu-servicio.northflank.app` |
| `DATABASE_URL` | `postgres://...` (de Neon) |

---

## 4. Deploy

Click **"Create Service"** y espera ~2-3 minutos.

---

## 5. Crear Superusuario

Después del deploy, en el **Shell** de Northflank:
```bash
python manage.py createsuperuser
```

---

## Dominio Personalizado (Opcional)

Northflank ofrece subdominio gratis: `tu-servicio.northflank.app`

Para dominio propio:
1. Settings → Domains
2. Agrega tu dominio
3. Configura DNS en Cloudflare
