#!/bin/bash
# =============================================================================
# Build Script - LogicPerfect
# =============================================================================

set -e

echo "========================================"
echo "LogicPerfect - Build Script"
echo "========================================"

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run migrations
echo "Running database migrations..."
python manage.py migrate

echo "========================================"
echo "Build completed successfully!"
echo "========================================"
