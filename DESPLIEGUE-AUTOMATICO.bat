@echo off
chcp 65001 >nul
set PATH=%PATH%;C:\Program Files\Git\cmd;C:\Program Files\Git\bin

echo.
echo ════════════════════════════════════════════════════════════
echo     LogicPerfect - Despliegue Automático Completo
echo     Marketplace de Proyectos de Programación
echo ════════════════════════════════════════════════════════════
echo.

echo [1/6] Verificando Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Git no encontrado
    pause
    exit /b 1
)
echo Git OK

echo.
echo [2/6] Cambiando a directorio del proyecto...
cd /d "%~dp0"
echo Directorio: %CD%

echo.
echo [3/6] Verificando repositorio...
git status >nul 2>&1
if errorlevel 1 (
    echo Inicializando Git...
    git init
    git add .
    git commit -m "LogicPerfect - Ecommerce Marketplace"
)

echo.
echo [4/6] Configurando remote...
git remote set-url origin https://github.com/PaulaFernandezJofre/FullStack.git >nul 2>&1
if errorlevel 1 (
    git remote add origin https://github.com/PaulaFernandezJofre/FullStack.git
)

echo.
echo [5/6] Subiendo a GitHub...
git push -u origin main --force
if errorlevel 1 (
    echo ERROR al subir a GitHub
    echo Verifica que el repositorio existe en GitHub
    pause
    exit /b 1
)

echo.
echo [6/6] Código subido exitosamente
echo.

echo ════════════════════════════════════════════════════════════
echo     PASOS PARA COMPLETAR EL DESPLIEGUE EN RENDER
echo ════════════════════════════════════════════════════════════
echo.
echo 1. Ve a: https://dashboard.render.com
echo.
echo 2. Crea PostgreSQL:
echo    - Click "New +" -^> "PostgreSQL"
echo    - Name: logicperfect-db
echo    - Plan: Free
echo    - Region: Oregon
echo    - Click "Create Database"
echo    - COPIA la "Internal Connection String"
echo.
echo 3. Crea Web Service:
echo    - Click "New +" -^> "Web Service"
echo    - Connect: PaulaFernandezJofre/FullStack
echo    - Region: Oregon
echo    - Environment: Python
echo    - Branch: main
echo.
echo 4. Configura en Environment:
echo    - PYTHON_VERSION = 3.12
echo    - DEBUG = False
echo    - DJANGO_SECRET_KEY = (genera una clave)
echo    - ALLOWED_HOSTS = logicperfect.onrender.com
echo    - DATABASE_URL = (pega connection string)
echo.
echo 5. Build Command:
echo    pip install -r requirements.txt ^&^& python manage.py collectstatic --noinput ^&^& python manage.py migrate
echo.
echo 6. Start Command:
echo    gunicorn devstack.wsgi:application --bind 0.0.0.0:$PORT --workers 2
echo.
echo 7. Click "Create Web Service"
echo    (Espera 2-3 minutos)
echo.
echo 8. Crea superusuario:
echo    - Ve al Shell del Web Service
echo    - python manage.py createsuperuser
echo.
echo ════════════════════════════════════════════════════════════
echo.

pause
