from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.UserLoginView.as_view(), name='login'),
    path('register/', views.UserRegistrationView.as_view(), name='register'),

    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('profile/update/', views.UserProfileUpdateView.as_view(),
         name='update-profile'),

    path('logout/', views.UserLogoutView.as_view(), name='logout'),

    path('customers/', views.CustomersListView.as_view(), name='customers'),
    path('engineers/', views.EngineersListView.as_view(), name='engineers'),
]
