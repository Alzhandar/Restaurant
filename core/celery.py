import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('restaurant_reservation')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

from celery.schedules import crontab

app.conf.beat_schedule = {
    'send-reservation-reminders-daily': {
        'task': 'reservations.tasks.send_reservation_reminders',
        'schedule': crontab(hour=8, minute=0),
    },
    'mark-no-shows-daily': {
        'task': 'reservations.tasks.mark_no_shows',
        'schedule': crontab(hour=23, minute=30),
    },
}
