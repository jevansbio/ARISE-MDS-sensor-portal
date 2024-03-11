from __future__ import absolute_import, unicode_literals

import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sensor_portal.settings")

app = Celery("sensor_portal")

app.config_from_object("django.conf:settings", namespace="CELERY")


app.autodiscover_tasks()




