from django.urls import path

from . import views

urlpatterns = [
    path('', views.BookingListCreateView.as_view(), name='booking-list'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('<int:pk>/status/', views.BookingStatusView.as_view(), name='booking-status'),
    path('engineers/<int:pk>/trust/', views.EngineerTrustView.as_view(), name='engineer-trust'),
    path('categories/', views.CategoriesView.as_view(), name='categories'),
    path('stats/', views.AdminStatsView.as_view(), name='admin-stats'),
]
