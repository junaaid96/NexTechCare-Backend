"""Engineer Trust Score (0-100).

Weights: rating 45%, completion rate 25%, response speed 20%, verified badge 10%.
New engineers with no history start from a neutral prior so they are not buried.
"""
from django.db.models import Avg


def trust_breakdown(engineer):
    from reviews.models import Review
    from .models import Booking

    reviews = Review.objects.filter(service__engineer=engineer)
    review_count = reviews.count()
    avg_rating = reviews.aggregate(a=Avg('rating'))['a']  # 1..10 scale
    rating_part = (avg_rating / 10.0) if avg_rating else 0.7

    bookings = Booking.objects.filter(service__engineer=engineer)
    closed = bookings.filter(status__in=['resolved', 'cancelled'])
    resolved = bookings.filter(status='resolved').count()
    completion = (resolved / closed.count()) if closed.count() else 0.8

    accepted = bookings.exclude(accepted_at=None)
    hours = [(b.accepted_at - b.created_at).total_seconds() / 3600 for b in accepted[:50]]
    avg_response_h = (sum(hours) / len(hours)) if hours else None
    # <=1h -> 1.0, 24h+ -> 0.2
    speed = 0.75 if avg_response_h is None else max(0.2, min(1.0, 1.0 - (avg_response_h - 1) / 29))

    verified = 1.0 if getattr(engineer, 'verified', False) else 0.0
    score = round(100 * (0.45 * rating_part + 0.25 * completion + 0.20 * speed + 0.10 * verified))
    return {
        'score': score,
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
        'review_count': review_count,
        'completion_rate': round(completion * 100),
        'jobs_completed': resolved,
        'avg_response_hours': round(avg_response_h, 1) if avg_response_h is not None else None,
        'verified': bool(verified),
    }
