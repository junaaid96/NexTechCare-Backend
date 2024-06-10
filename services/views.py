from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from nextechcare_drf.permissions import IsEngineer, IsCustomer
from .models import Service
from .serializers import ServiceSerializer, ServiceCreateUpdateSerializer
from profiles.models import EngineerProfile, CustomerProfile


# GET and POST requests for the retrieval and creation of Service instances.
class ServiceListCreateView(generics.ListCreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsEngineer()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ServiceCreateUpdateSerializer
        return ServiceSerializer

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(
                engineer=EngineerProfile.objects.get(user=request.user))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# GET, PUT, and DELETE requests allowing for the retrieval, update, and deletion of a single Service instance.
class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsEngineer()]

    def get_serializer_class(self):
        if self.request.method == 'PUT':
            return ServiceCreateUpdateSerializer
        return ServiceSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        engineer = EngineerProfile.objects.get(user=request.user)
        service = self.get_object()
        service.engineer = engineer
        service.name = serializer.validated_data.get('name', service.name)
        service.description = serializer.validated_data.get(
            'description', service.description)
        service.price = serializer.validated_data.get('price', service.price)
        service.duration = serializer.validated_data.get(
            'duration', service.duration)
        service.save()
        return Response(ServiceSerializer(service).data, status=status.HTTP_200_OK)


class ServiceTakenCreateView(generics.CreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsCustomer]

    def create(self, request, pk):
        service = Service.objects.get(pk=pk)
        customer = CustomerProfile.objects.get(user=request.user)
        if service.customer.filter(user=request.user).exists():
            return Response({'error': 'Service already taken!'}, status=status.HTTP_400_BAD_REQUEST)
        service.customer.add(customer)
        return Response({'success': 'Service taken successfully!'}, status=status.HTTP_200_OK)
