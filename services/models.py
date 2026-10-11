from django.db import models
from profiles.models import EngineerProfile, CustomerProfile


CATEGORY_CHOICES = [
    ('software', 'Software Support'),
    ('hardware', 'Hardware Repair'),
    ('consultancy', 'IT Consultancy'),
    ('data_recovery', 'Data Recovery'),
    ('networking', 'Networking & Wi-Fi'),
    ('cybersecurity', 'Cybersecurity'),
    ('cloud_backup', 'Cloud & Backup'),
    ('device_setup', 'Device Setup'),
    ('smart_home', 'Smart Home & IoT'),
    ('remote_support', 'Remote Support'),
]


class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration = models.PositiveIntegerField()
    engineer = models.ForeignKey(EngineerProfile, on_delete=models.CASCADE)
    admin_approved = models.BooleanField(default=False)
    customer = models.ManyToManyField(CustomerProfile, blank=True)
    category = models.CharField(max_length=32, choices=CATEGORY_CHOICES, default='software', db_index=True)
    sla_hours = models.PositiveIntegerField(default=24, help_text='Target hours from booking to resolution')
    is_remote = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ['-id']

    def __str__(self):
        return f'{self.name} by {self.engineer.user.first_name} {self.engineer.user.last_name}'
