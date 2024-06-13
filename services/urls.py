from django.urls import path
from .views import ServiceListCreateView, ServiceDetailView, ServiceTakenCreateView, ServiceApprovedCreateView

urlpatterns = [
    path('', ServiceListCreateView.as_view(), name='service-list-create'),
    path('<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
    path('taken/<int:pk>/', ServiceTakenCreateView.as_view(), name='service-taken'),
    path('approved/<int:pk>/', ServiceApprovedCreateView.as_view(),
         name='service-approved'),
]
