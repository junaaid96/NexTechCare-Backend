from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Review
from activities.models import Activity
from services.models import Service
from .serializers import ReviewSerializer, ReviewCreateSerializer
from profiles.models import CustomerProfile
from nextechcare_drf.permissions import IsCustomer


class ReviewListCreateView(generics.ListCreateAPIView):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsCustomer()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ReviewCreateSerializer
        return ReviewSerializer

    def list(self, request, pk):
        service = Service.objects.get(pk=pk)
        reviews = Review.objects.filter(service=service)
        serializer = self.get_serializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        customer = CustomerProfile.objects.get(user=request.user)
        service = Service.objects.get(pk=pk)
        if not service.customer.filter(pk=customer.pk).exists():
            return Response({'error': 'You cannot review a service you have not taken.'}, status=status.HTTP_400_BAD_REQUEST)
        if Review.objects.filter(customer=customer, service=service).exists():
            return Response({'error': 'You have already reviewed this service.'}, status=status.HTTP_400_BAD_REQUEST)
        Review.objects.create(
            customer=customer, service=service, **serializer.validated_data)
        Activity.objects.create(
            name=f'{customer.user.first_name} {customer.user.last_name} reviewed {service.name}')
        return Response({'success': 'Review created successfully.'}, status=status.HTTP_201_CREATED)
