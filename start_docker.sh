#!/bin/bash

# Kill all processes on port 8000
fuser -k 8000/tcp
sleep 1

# Start Redis
redis-server --daemonize yes
sleep 5  # Adjust sleep time as needed for Redis to start

# Navigate to Django project directory
cd vlp

# Start Celery worker
celery -A server worker --loglevel=info &

# Start Celery Beat if needed
celery -A server beat --loglevel=info &

# Start Django with Gunicorn
gunicorn --bind 0.0.0.0:8000 server.wsgi:application

# Keep the shell open
wait
