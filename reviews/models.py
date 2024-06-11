from django.db import models
from profiles.models import CustomerProfile
from services.models import Service

RATING_CHOICES = [(i, i) for i in range(1, 11)]


class Review(models.Model):
    customer = models.ForeignKey(
        CustomerProfile, on_delete=models.CASCADE, null=True)
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.customer.user.username} - {self.service.name} - {self.rating}'

    class Meta:
        ordering = ['-created_at']
