from django.urls import path

from .views import TriageView

urlpatterns = [path('', TriageView.as_view(), name='triage')]
