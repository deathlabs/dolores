#!/usr/bin/env sh

set -e

python manage.py migrate

uvicorn dolores.asgi:application --host 0.0.0.0 --port 8000
