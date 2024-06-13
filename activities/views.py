from rest_framework import generics
from nextechcare_drf.permissions import IsCustomAdmin
from .models import Activity
from .serializers import ActivitySerializer


class ActivityListView(generics.ListAPIView):
    queryset = Activity.objects.all()
    serializer_class = ActivitySerializer
    permission_classes = [IsCustomAdmin]
