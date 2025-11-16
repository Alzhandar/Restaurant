from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model

User = get_user_model()


@shared_task(name='users.tasks.send_welcome_email')
def send_welcome_email(user_id):
    try:
        user = User.objects.get(id=user_id)
        subject = 'Добро пожаловать в Restaurant Reservation'
        message = (
            f'Здравствуйте, {user.first_name or user.email}!\n\n'
            'Спасибо за регистрацию в нашей системе бронирования.\n'
            'Желаем приятного пользования сервисом!\n'
        )
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        send_mail(subject, message, from_email, [user.email], fail_silently=False)
        return True
    except Exception as e:
        return str(e)
