from django.contrib import admin
from .models import Service


class ServiceAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration', 'engineer', 'admin_approved']
    search_fields = ['name', 'price', 'duration', 'engineer', 'admin_approved']


admin.site.register(Service, ServiceAdmin)
