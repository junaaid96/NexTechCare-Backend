from django.db import models
from profiles.models import EngineerProfile, CustomerProfile


class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=5, decimal_places=2)
    duration = models.DurationField()
    review_text = models.TextField(blank=True)
    engineer = models.ForeignKey(EngineerProfile, on_delete=models.CASCADE)
    admin_approved = models.BooleanField(default=False)
    customer = models.ManyToManyField(CustomerProfile, blank=True)

    def __str__(self):
        return f'{self.name} by {self.engineer.user.first_name} {self.engineer.user.last_name}'
