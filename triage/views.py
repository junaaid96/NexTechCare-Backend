from rest_framework import permissions, serializers, status
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from services.models import Service
from services.serializers import ServiceSerializer

from .engine import triage


class TriageThrottle(AnonRateThrottle):
    scope = 'triage'

    def get_cache_key(self, request, view):
        return self.cache_format % {'scope': self.scope, 'ident': self.get_ident(request)}


class TriageInput(serializers.Serializer):
    description = serializers.CharField(min_length=8, max_length=2000)


class TriageView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [TriageThrottle]

    def post(self, request):
        ser = TriageInput(data=request.data)
        ser.is_valid(raise_exception=True)
        result = triage(ser.validated_data['description'])
        services = Service.objects.filter(pk__in=result['recommended_service_ids'], admin_approved=True)
        by_id = {s.pk: s for s in services}
        result['services'] = [ServiceSerializer(by_id[i]).data for i in result['recommended_service_ids'] if i in by_id]
        return Response(result, status=status.HTTP_200_OK)
