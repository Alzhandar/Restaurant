from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


@shared_task(name='reservations.tasks.send_reservation_reminders')
def send_reservation_reminders():
    from .models import Reservation, ReservationStatus

    tomorrow = timezone.now().date() + timedelta(days=1)
    qs = Reservation.objects.filter(
        date=tomorrow,
        status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
        reminder_sent=False,
    ).select_related('user', 'restaurant')

    results = []
    for r in qs:
        try:
            subject = f'Напоминание о бронировании в {r.restaurant.name} на {r.date}'
            message = (
                f'Здравствуйте, {r.user.first_name or r.user.email}!\n\n'
                f'Напоминаем о вашем бронировании в ресторане {r.restaurant.name} ' 
                f'на {r.date} в {r.time_slot}.\n\n'
                'Если нужно отменить или изменить — пожалуйста, используйте ваш профиль.'
            )
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
            send_mail(subject, message, from_email, [r.user.email], fail_silently=False)
            r.reminder_sent = True
            r.save(update_fields=['reminder_sent'])
            results.append((r.id, 'sent'))
        except Exception as e:
            results.append((r.id, str(e)))

    return results


@shared_task(name='reservations.tasks.mark_no_shows')
def mark_no_shows():
    from .models import Reservation, ReservationStatus
    delta_minutes = 60 
    now = timezone.now()
    cutoff = now - timedelta(minutes=delta_minutes)

    qs = Reservation.objects.filter(
        status=ReservationStatus.CONFIRMED,
        date__lt=now.date()
    )
    updated = []
    for r in qs:
        try:
            r.status = ReservationStatus.NO_SHOW
            r.save(update_fields=['status'])
            updated.append(r.id)
        except Exception:
            continue

    return updated
