# =============================================================================
# Procfile - Render.com Deployment
# =============================================================================
# This file tells Render how to run your application

# Web server
web: gunicorn devstack.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4

# Background worker (optional - for Celery)
# worker: celery -A devstack worker -l info
