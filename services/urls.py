from django.urls import path
from .views import ServiceListCreateView, ServiceDetailView, ServiceTakenCreateView, ServiceApprovedCreateView, ServiceBulkApproveView, ServiceRejectView

urlpatterns = [
    path('', ServiceListCreateView.as_view(), name='service-list-create'),
    path('<int:pk>/', ServiceDetailView.as_view(), name='service-detail'),
    path('taken/<int:pk>/', ServiceTakenCreateView.as_view(), name='service-taken'),
    path('approved/<int:pk>/', ServiceApprovedCreateView.as_view(),
         name='service-approved'),
    path('approved/bulk/', ServiceBulkApproveView.as_view(), name='service-bulk-approve'),
    path('rejected/<int:pk>/', ServiceRejectView.as_view(), name='service-reject'),
]
