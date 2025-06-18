#!/bin/sh
set -e

echo "Applying database migrations..."
uv run manage.py migrate --no-input

echo "Compiling translation messages..."
uv run manage.py compilemessages

echo "Starting application..."
exec "$@"
