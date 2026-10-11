from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),

    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(),
         name='update-profile'),

    path('demo-login/', views.DemoLoginView.as_view(), name='demo-login'),
    path('demo/reset/', views.DemoResetView.as_view(), name='demo-reset'),
    path('logout/', views.UserLogoutView.as_view(), name='logout'),

    path('customers/', views.CustomersListView.as_view(), name='customers'),
    path('engineers/', views.EngineersListView.as_view(), name='engineers'),
    path('engineers/<int:pk>/verify/', views.EngineerVerifyView.as_view(), name='engineer-verify'),
]
