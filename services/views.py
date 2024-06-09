from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from nextechcare_drf.permissions import IsEngineer, IsCustomer
from .models import Service
from .serializers import ServiceSerializer, ServiceCreateSerializer, ServiceUpdateSerializer
from profiles.models import EngineerProfile, CustomerProfile
from profiles.serializers import EngineerProfileSerializer, CustomerProfileSerializer
# from reviews.models import Review
# from reviews.serializers import ReviewSerializer


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
            return ServiceCreateSerializer
        return ServiceSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        engineer_data = serializer.validated_data.pop('engineer')
        engineer = EngineerProfile.objects.get(**engineer_data)
        service = Service.objects.create(
            engineer=engineer, **serializer.validated_data)
        return Response(ServiceSerializer(service).data, status=status.HTTP_201_CREATED)


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
            return ServiceUpdateSerializer
        return ServiceSerializer

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        engineer_data = serializer.validated_data.pop('engineer')
        engineer = EngineerProfile.objects.get(**engineer_data)
        service = self.get_object()
        service.engineer = engineer
        service.name = serializer.validated_data.get('name', service.name)
        service.description = serializer.validated_data.get(
            'description', service.description)
        service.price = serializer.validated_data.get('price', service.price)
        service.duration = serializer.validated_data.get(
            'duration', service.duration)
        service.review_text = serializer.validated_data.get(
            'review_text', service.review_text)
        service.admin_approved = serializer.validated_data.get(
            'admin_approved', service.admin_approved)
        service.save()
        return Response(ServiceSerializer(service).data, status=status.HTTP_200_OK)


# class ServiceReviewCreateView(generics.CreateAPIView):
#     queryset = Review.objects.all()
#     serializer_class = ReviewSerializer

#     def get_permissions(self):
#         if self.request.method == 'POST':
#             return [permissions.IsAuthenticated()]
#         return [permissions.AllowAny()]

#     def create(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         user = CustomerProfile.objects.get(user=request.user)
#         service = Service.objects.get(id=self.kwargs['pk'])
#         review = Review.objects.create(
#             user=user, service=service, **serializer.validated_data)
#         return Response(ReviewSerializer(review).data, status=status.HTTP_201_CREATED)


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
