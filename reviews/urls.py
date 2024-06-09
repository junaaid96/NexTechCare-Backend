from django.urls import path
from .views import ReviewListCreateView


urlpatterns = [
    path('<int:pk>/', ReviewListCreateView.as_view(), name='review-list-create'),
]
