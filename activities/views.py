from rest_framework import generics
from nextechcare_drf.permissions import IsCustomAdmin
from .models import Activity
from .serializers import ActivitySerializer


class ActivityListView(generics.ListAPIView):
    def get_queryset(self):
        from profiles.demo import is_demo
        qs = Activity.objects.all()
        if is_demo(self.request.user):
            qs = qs.filter(name__icontains='(demo)')
        return qs

    serializer_class = ActivitySerializer
    permission_classes = [IsCustomAdmin]
