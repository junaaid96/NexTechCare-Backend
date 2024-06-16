from django.contrib import admin
from .models import ContactText


class ContactTextAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject')
    list_filter = ('name', 'email', 'subject')
    search_fields = ('name', 'email', 'subject')


admin.site.register(ContactText, ContactTextAdmin)
