from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import User, AdminProfile, CustomerProfile, EngineerProfile
from .serializers import AdminProfileSerializer, CustomerProfileSerializer, EngineerProfileSerializer, UserRegistrationSerializer, CustomerProfileUpdateSerializer, EngineerProfileUpdateSerializer, UserLoginSerializer
from django.contrib.auth import authenticate, login, logout
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from django.conf import settings
from django.db.models import Q
from rest_framework.throttling import AnonRateThrottle
from nextechcare_drf.permissions import IsCustomAdmin
from .demo import DEMO_ACCOUNTS, DEMO_PREFIX, is_demo, block_if_demo


class _DemoScopedList(generics.ListAPIView):
    """The demo admin only sees demo users, never real people's details."""
    permission_classes = [IsCustomAdmin]

    def get_queryset(self):
        qs = self.model.objects.select_related('user')
        if is_demo(self.request.user):
            qs = qs.filter(user__username__startswith=DEMO_PREFIX)
        return qs


class CustomersListView(_DemoScopedList):
    model = CustomerProfile
    serializer_class = CustomerProfileSerializer


class EngineersListView(_DemoScopedList):
    model = EngineerProfile
    serializer_class = EngineerProfileSerializer


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

    def update(self, request, *args, **kwargs):
        block_if_demo(request, 'Demo profiles are read-only.')
        return super().update(request, *args, **kwargs)

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
        eng = EngineerProfile.objects.filter(pk=pk).select_related('user').first()
        if eng and is_demo(request.user) and not eng.user.username.startswith(DEMO_PREFIX):
            return Response({'error': 'The demo admin can only manage demo users.'}, status=status.HTTP_403_FORBIDDEN)
        if not eng:
            return Response({'error': 'Engineer not found.'}, status=status.HTTP_404_NOT_FOUND)
        eng.verified = not eng.verified
        eng.save(update_fields=['verified'])
        return Response({'verified': eng.verified}, status=status.HTTP_200_OK)


class DemoLoginThrottle(AnonRateThrottle):
    scope = 'demo_login'


class DemoLoginView(generics.GenericAPIView):
    """One-click demo login. No password ever reaches the browser."""
    throttle_classes = [DemoLoginThrottle]

    def post(self, request):
        role = str(request.data.get('role', '')).upper()[:1]
        username = DEMO_ACCOUNTS.get(role)
        user = User.objects.filter(username=username, is_active=True).first() if username else None
        if not user:
            return Response({'error': 'Demo is not available right now.'}, status=status.HTTP_404_NOT_FOUND)
        return Response({'refresh': str(RefreshToken.for_user(user)), 'access': str(AccessToken.for_user(user)),
                         'user_id': user.id, 'user_type': user.user_type, 'demo': True}, status=status.HTTP_200_OK)


class DemoResetView(generics.GenericAPIView):
    """Nightly reset, called by Vercel Cron with `Authorization: Bearer $CRON_SECRET`."""

    def get(self, request):
        secret = getattr(settings, 'CRON_SECRET', '')
        if not secret or request.headers.get('Authorization') != f'Bearer {secret}':
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        from django.core.management import call_command
        call_command('seed_demo')
        return Response({'reset': True})
