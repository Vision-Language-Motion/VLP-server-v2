#!/bin/bash

# Kill all processes on port 8000
fuser -k 8000/tcp
sleep 1

# Start Redis
redis-server &

cd vlp
# Start Django
python3 manage.py runserver &

# Start Celery
celery -A server worker --loglevel=info &

celery -A server beat --loglevel=warning &
# Start Celery Beat if needed
# echo "Starting Celery Beat..."
# celery -A server beat --loglevel=info &

echo "Django and Celery are running."

# Keep the shell open
wait