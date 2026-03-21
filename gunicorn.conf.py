# =============================================================================
# Gunicorn Configuration - LogicPerfect
# =============================================================================

import multiprocessing

# Binding
bind = '0.0.0.0:8000'

# Workers (2-4 workers recommended)
workers = int(os.getenv('GUNICORN_WORKERS', 2))

# Threads per worker (for I/O bound apps)
threads = int(os.getenv('GUNICORN_THREADS', 4))

# Timeout
timeout = 120

# Keepalive
keepalive = 5

# Graceful timeout
graceful_timeout = 30

# Max requests per worker (recycle to prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'warning'

# Worker class
worker_class = 'sync'

# Preload app
preload_app = True

# Daemon mode (don't use with Render)
daemon = False
