from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from profiles.models import CustomerProfile
from services.models import Service

STATUS_CHOICES = [
    ('requested', 'Requested'),
    ('accepted', 'Accepted'),
    ('in_progress', 'In progress'),
    ('resolved', 'Resolved'),
    ('cancelled', 'Cancelled'),
]
PRIORITY_CHOICES = [('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('critical', 'Critical')]

# Allowed transitions: who can move a booking to which status.
ENGINEER_TRANSITIONS = {
    'requested': ['accepted', 'cancelled'],
    'accepted': ['in_progress', 'cancelled'],
    'in_progress': ['resolved'],
}
CUSTOMER_TRANSITIONS = {'requested': ['cancelled'], 'accepted': ['cancelled']}


class Booking(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='bookings')
    customer = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE, related_name='bookings')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='requested', db_index=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='normal')
    issue = models.TextField(blank=True)
    triage_summary = models.TextField(blank=True)
    preferred_time = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    sla_due_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.sla_due_at:
            base = self.created_at or timezone.now()
            self.sla_due_at = base + timedelta(hours=self.service.sla_hours or 24)
        super().save(*args, **kwargs)

    @property
    def sla_breached(self):
        end = self.resolved_at or timezone.now()
        return bool(self.sla_due_at and end > self.sla_due_at and self.status != 'cancelled')

    def __str__(self):
        return f'#{self.pk} {self.service.name} ({self.status})'


class BookingEvent(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES)
    note = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
