from celery import Celery
from celery.schedules import crontab
import os
from .settings import INSTALLED_APPS

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

app = Celery('server', include=['api.tasks'])
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks(lambda: INSTALLED_APPS)
app.conf.result_backend = 'redis://localhost:6379/0'
app.conf.broker_connection_retry_on_startup = True

# Wird auf dem Cluster processed
'''
    'process-urls-every-hour': {
        'task': 'api.tasks.process_urls',
        'schedule': crontab(minute=0, hour='*/1'),  # Executes every hour
        # 'schedule': crontab(minute='*/1'),  # Debugging: Runs every Mintue

    },
'''