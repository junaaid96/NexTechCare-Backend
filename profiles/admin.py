from django.contrib import admin
from .models import User, AdminProfile, CustomerProfile, EngineerProfile

admin.site.register(User)


class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address', 'task']
    search_fields = ['user__username', 'user__first_name',
                     'user__last_name', 'phone', 'address', 'task']


admin.site.register(AdminProfile, AdminProfileAdmin)


class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address', 'occupation']
    search_fields = ['user__username', 'user__first_name',
                     'user__last_name', 'phone', 'address', 'occupation']


admin.site.register(CustomerProfile, CustomerProfileAdmin)


class EngineerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'address', 'skills', 'experience']
    search_fields = ['user__username', 'user__first_name',
                     'user__last_name', 'phone', 'address', 'skills', 'experience']


admin.site.register(EngineerProfile, EngineerProfileAdmin)
