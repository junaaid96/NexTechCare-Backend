from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from nextechcare_drf.permissions import IsEngineer, IsCustomer, IsCustomAdmin
from .models import Service
from activities.models import Activity
from .serializers import ServiceSerializer, ServiceCreateUpdateSerializer
from profiles.models import EngineerProfile, CustomerProfile
from rest_framework import filters


# GET and POST requests for the retrieval and creation of Service instances.
# pagination will be added late.
class ServiceListCreateView(generics.ListCreateAPIView):
    serializer_class = ServiceSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description',
                     'engineer__user__first_name', 'engineer__user__last_name']

    def get_queryset(self):
        queryset = Service.objects.all()
        engineer = self.request.query_params.get('engineer')
        customer = self.request.query_params.get('customer')
        admin_approved = self.request.query_params.get('admin_approved')

        if engineer:
            queryset = queryset.filter(engineer__user__username=engineer)
        if customer:
            queryset = queryset.filter(customer__user__username=customer)
        if admin_approved:
            queryset = queryset.filter(admin_approved=admin_approved)
        return queryset

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
            Activity.objects.create(
                name=f'{request.user.first_name} {request.user.last_name} created a service named {serializer.validated_data.get("name")} and pending for admin approval!')
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

        service = self.get_object()
        engineer = EngineerProfile.objects.get(user=request.user)
        if service.engineer != engineer:
            return Response({'error': 'You are not allowed to update this service!'}, status=status.HTTP_403_FORBIDDEN)

        serializer.is_valid(raise_exception=True)
        service.name = serializer.validated_data.get('name', service.name)
        service.description = serializer.validated_data.get(
            'description', service.description)
        service.price = serializer.validated_data.get('price', service.price)
        service.duration = serializer.validated_data.get(
            'duration', service.duration)
        service.save()
        Activity.objects.create(
            name=f'{engineer.user.first_name} {engineer.user.last_name} updated a service named {service.name}!')
        return Response(ServiceSerializer(service).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        service = self.get_object()
        engineer = EngineerProfile.objects.get(user=request.user)

        if service.engineer != engineer:
            return Response({'error': 'You are not allowed to delete this service!'}, status=status.HTTP_403_FORBIDDEN)

        service.delete()
        Activity.objects.create(
            name=f'{request.user.first_name} {request.user.last_name} deleted a service named {service.name}!')
        return Response({'success': 'Service deleted successfully!'}, status=status.HTTP_200_OK)


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
        service.save()
        Activity.objects.create(
            name=f'{customer.user.first_name} {customer.user.last_name} took a service named {service.name}!')
        return Response({'success': 'Service taken successfully!'}, status=status.HTTP_200_OK)


class ServiceApprovedCreateView(generics.CreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsCustomAdmin]

    def create(self, request, pk):
        service = Service.objects.get(pk=pk)
        service.admin_approved = True
        service.save()
        Activity.objects.create(
            name=f'{request.user.first_name} {request.user.last_name} approved a service named {service.name}!')
        return Response({'success': 'Service approved successfully!'}, status=status.HTTP_200_OK)
