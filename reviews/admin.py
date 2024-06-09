from django.contrib import admin
from .models import Review


class ReviewAdmin(admin.ModelAdmin):
    list_display = ['customer', 'service', 'rating', 'created_at']
    search_fields = ['customer__user__username', 'service__name']


admin.site.register(Review, ReviewAdmin)
