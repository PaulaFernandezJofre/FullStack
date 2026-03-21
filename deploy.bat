@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ════════════════════════════════════════════════════════════
echo     LogicPerfect - Despliegue Automático
echo     Marketplace de Proyectos de Programación
echo ════════════════════════════════════════════════════════════
echo.

:: Verificar Git
echo [1/5] Verificando Git...
where git >nul 2>&1
if errorlevel 1 (
    echo ❌ Git no encontrado. Por favor instala Git primero.
    echo    Descarga de: https://git-scm.com/download/win
    pause
    exit /b 1
)
echo ✅ Git encontrado

:: Verificar que estamos en el directorio correcto
echo.
echo [2/5] Verificando proyecto...
if not exist "manage.py" (
    echo ❌ Este script debe ejecutarse desde la carpeta del proyecto
    pause
    exit /b 1
)
if not exist "render.yaml" (
    echo ❌ Archivo render.yaml no encontrado
    pause
    exit /b 1
)
echo ✅ Proyecto verificado

:: Mostrar estado de Git
echo.
echo [3/5] Estado de Git...
git status >nul 2>&1
if errorlevel 1 (
    echo 🔄 Inicializando repositorio Git...
    git init
    git add .
    git commit -m "LogicPerfect - Ecommerce Marketplace"
) else (
    echo ✅ Repositorio Git ya existe
    git status --short
)

:: Solicitar nombre de usuario GitHub
echo.
echo [4/5] Configurando GitHub...
echo.
set /p GH_USER="Ingresa tu usuario de GitHub: "
if "!GH_USER!"=="" (
    echo ❌ Usuario requerido
    pause
    exit /b 1
)

:: Crear repositorio en GitHub
echo.
echo [5/5] Creando repositorio en GitHub...
echo.

:: Verificar si gh CLI está disponible
where gh >nul 2>&1
if errorlevel 1 (
    echo ⚠️ GitHub CLI (gh) no encontrado
    echo.
    echo Para crear el repositorio manualmente:
    echo 1. Ve a: https://github.com/new
    echo 2. Repository name: logicperfect
    echo 3. Select: Public
    echo 4. Click: Create repository
    echo 5. Ejecuta los siguientes comandos:
    echo.
    echo    git remote add origin https://github.com/!GH_USER!/logicperfect.git
    echo    git branch -M main
    echo    git push -u origin main
    echo.
    set /p CONTINUE="¿Ya creaste el repositorio en GitHub? (s/n): "
    if /i "!CONTINUE!"=="s" (
        git remote add origin https://github.com/!GH_USER!/logicperfect.git
        git branch -M main
        git push -u origin main
    )
) else (
    echo Usando GitHub CLI...
    gh repo create logicperfect --public --source=. --push
)

echo.
echo ════════════════════════════════════════════════════════════
echo     Código subido a GitHub
echo ════════════════════════════════════════════════════════════
echo.

:: Instrucciones para Render
echo.
echo ════════════════════════════════════════════════════════════
echo     PRÓXIMOS PASOS - Render.com
echo ════════════════════════════════════════════════════════════
echo.
echo 1. Ve a: https://render.com
echo 2. Inicia sesión con GitHub
echo 3. Click: "New +" ^> "PostgreSQL"
echo    - Name: logicperfect-db
echo    - Plan: Free
echo    - Click: "Create Database"
echo 4. Click: "New +" ^> "Blueprint"
echo 5. Sube el archivo: render.yaml
echo 6. Click: "Apply"
echo.
echo La aplicación se desplegará automáticamente.
echo.
echo Una vez desplegado, crea el superusuario:
echo - Ve a tu Web Service en Render
echo - Click: "Shell"
echo - Ejecuta: python manage.py createsuperuser
echo.
echo ════════════════════════════════════════════════════════════
echo     ¡Listo! Tu marketplace está en línea
echo ════════════════════════════════════════════════════════════
echo.

pause
