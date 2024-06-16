from django.urls import path
from .views import ContactTextCreateView, ContactTextListView

urlpatterns = [
    path('contact/', ContactTextCreateView.as_view(), name='contact-create'),
    path('contact/list/', ContactTextListView.as_view(), name='contact-list'),
]
