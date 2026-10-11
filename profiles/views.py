from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import User, AdminProfile, CustomerProfile, EngineerProfile
from .serializers import AdminProfileSerializer, CustomerProfileSerializer, EngineerProfileSerializer, UserRegistrationSerializer, CustomerProfileUpdateSerializer, EngineerProfileUpdateSerializer, UserLoginSerializer
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from nextechcare_drf.permissions import IsCustomAdmin


class CustomersListView(generics.ListAPIView):
    queryset = CustomerProfile.objects.all()
    serializer_class = CustomerProfileSerializer
    permission_classes = [IsCustomAdmin]


class EngineersListView(generics.ListAPIView):
    queryset = EngineerProfile.objects.all()
    serializer_class = EngineerProfileSerializer
    permission_classes = [IsCustomAdmin]


class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.user_type == 'C':
            return CustomerProfileSerializer
        elif self.request.user.user_type == 'E':
            return EngineerProfileSerializer
        elif self.request.user.user_type == 'A':
            return AdminProfileSerializer

    def get_object(self):
        if self.request.user.user_type == 'C':
            return CustomerProfile.objects.get(user=self.request.user)
        elif self.request.user.user_type == 'E':
            return EngineerProfile.objects.get(user=self.request.user)
        elif self.request.user.user_type == 'A':
            return AdminProfile.objects.get(user=self.request.user)


class UserProfileUpdateView(generics.UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.user_type == 'C':
            return CustomerProfileUpdateSerializer
        elif self.request.user.user_type == 'E':
            return EngineerProfileUpdateSerializer

    def get_object(self):
        if self.request.user.user_type == 'C':
            return CustomerProfile.objects.get(user=self.request.user)
        elif self.request.user.user_type == 'E':
            return EngineerProfile.objects.get(user=self.request.user)


class UserLoginView(generics.CreateAPIView):
    serializer_class = UserLoginSerializer

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'error': 'User not found!'}, status=status.HTTP_400_BAD_REQUEST)

            if not user.is_active:
                return Response({'error': 'Please activate your account before login!'}, status=status.HTTP_400_BAD_REQUEST)

            user = authenticate(username=username, password=password)

            if user is not None:
                refresh = RefreshToken.for_user(user)
                access = AccessToken.for_user(user)
                return Response({'refresh': str(refresh), 'access': str(access), 'user_id': user.id, 'user_type': user.user_type}, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Invalid credentials! Try Again.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLogoutView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        return Response({'success': 'Logout successful!'}, status=status.HTTP_200_OK)


class EngineerVerifyView(generics.GenericAPIView):
    permission_classes = [IsCustomAdmin]

    def post(self, request, pk):
        eng = EngineerProfile.objects.filter(pk=pk).first()
        if not eng:
            return Response({'error': 'Engineer not found.'}, status=status.HTTP_404_NOT_FOUND)
        eng.verified = not eng.verified
        eng.save(update_fields=['verified'])
        return Response({'verified': eng.verified}, status=status.HTTP_200_OK)
