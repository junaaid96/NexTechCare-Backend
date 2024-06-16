from django.urls import path
from .views import ContactTextCreateView, ContactTextListView

urlpatterns = [
    path('', ContactTextListView.as_view(), name='contact-list'),
    path('create/', ContactTextCreateView.as_view(), name='contact-create'),
]
