from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Count, Avg
from django.utils import timezone


@shared_task(name='restaurants.tasks.generate_restaurant_report')
def generate_restaurant_report(restaurant_id):
    from .models import Restaurant
    from reservations.models import Reservation
    from reviews.models import Review

    try:
        restaurant = Restaurant.objects.get(id=restaurant_id)
        
        total_reservations = Reservation.objects.filter(restaurant=restaurant).count()
        completed = Reservation.objects.filter(
            restaurant=restaurant, status='completed'
        ).count()
        
        reviews = Review.objects.filter(restaurant=restaurant)
        total_reviews = reviews.count()
        avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
        
        report_text = (
            f"Отчёт для ресторана: {restaurant.name}\n"
            f"Дата генерации: {timezone.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            f"Всего бронирований: {total_reservations}\n"
            f"Завершённых бронирований: {completed}\n"
            f"Всего отзывов: {total_reviews}\n"
            f"Средний рейтинг: {round(avg_rating, 2)}\n"
        )
        
        subject = f'Отчёт для {restaurant.name}'
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        send_mail(subject, report_text, from_email, [restaurant.owner.email], fail_silently=False)
        
        return f"Report sent to {restaurant.owner.email}"
    except Exception as e:
        return str(e)
