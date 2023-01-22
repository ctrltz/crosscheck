import os

from celery import Celery


celery_app = Celery(__name__,
                    broker=os.environ.get('REDIS_URL', 'redis://localhost:6379'),
                    backend=os.environ.get('REDIS_URL', 'redis://localhost:6379'))
