from django.db.models import Count, Avg, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from activities.models import Activity
from nextechcare_drf.permissions import IsCustomAdmin
from profiles.models import CustomerProfile, EngineerProfile
from reviews.models import Review
from services.models import Service, CATEGORY_CHOICES

from .models import Booking, BookingEvent, ENGINEER_TRANSITIONS, CUSTOMER_TRANSITIONS
from .serializers import BookingSerializer, BookingCreateSerializer, StatusUpdateSerializer
from .trust import trust_breakdown


def _name(u):
    return f'{u.first_name} {u.last_name}'.strip() or u.username


class BookingListCreateView(APIView):
    """GET: bookings visible to the current user. POST (customer): book a service."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Booking.objects.select_related('service__engineer__user', 'customer__user').prefetch_related('events__actor')
        t = request.user.user_type
        if t == 'C':
            qs = qs.filter(customer__user=request.user)
        elif t == 'E':
            qs = qs.filter(service__engineer__user=request.user)
        st = request.query_params.get('status')
        if st:
            qs = qs.filter(status=st)
        return Response(BookingSerializer(qs[:200], many=True).data)

    def post(self, request):
        if request.user.user_type != 'C':
            return Response({'error': 'Only customers can book services.'}, status=status.HTTP_403_FORBIDDEN)
        ser = BookingCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        service = get_object_or_404(Service, pk=d['service'], admin_approved=True)
        customer = CustomerProfile.objects.get(user=request.user)
        if Booking.objects.filter(service=service, customer=customer, status__in=['requested', 'accepted', 'in_progress']).exists():
            return Response({'error': 'You already have an open booking for this service.'}, status=status.HTTP_400_BAD_REQUEST)
        b = Booking.objects.create(service=service, customer=customer, issue=d.get('issue', ''),
                                   triage_summary=d.get('triage_summary', ''), priority=d['priority'],
                                   preferred_time=d.get('preferred_time'))
        BookingEvent.objects.create(booking=b, status='requested', actor=request.user, note='Booking requested')
        service.customer.add(customer)  # keep legacy "taken" relation in sync
        Activity.objects.create(name=f'{_name(request.user)} booked {service.name}')
        return Response(BookingSerializer(b).data, status=status.HTTP_201_CREATED)


class BookingDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def _get(self, request, pk):
        b = get_object_or_404(Booking.objects.select_related('service__engineer__user', 'customer__user'), pk=pk)
        u = request.user
        if u.user_type == 'A' or b.customer.user_id == u.id or b.service.engineer.user_id == u.id:
            return b
        return None

    def get(self, request, pk):
        b = self._get(request, pk)
        if not b:
            return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        return Response(BookingSerializer(b).data)


class BookingStatusView(BookingDetailView):
    def post(self, request, pk):
        b = self._get(request, pk)
        if not b:
            return Response({'error': 'Not allowed.'}, status=status.HTTP_403_FORBIDDEN)
        ser = StatusUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        new = ser.validated_data['status']
        u = request.user
        if u.user_type == 'E':
            allowed = ENGINEER_TRANSITIONS.get(b.status, [])
        elif u.user_type == 'C':
            allowed = CUSTOMER_TRANSITIONS.get(b.status, [])
        else:
            allowed = ENGINEER_TRANSITIONS.get(b.status, []) + ['cancelled']
        if new not in allowed:
            return Response({'error': f'Cannot move from {b.status} to {new}.'}, status=status.HTTP_400_BAD_REQUEST)
        now = timezone.now()
        b.status = new
        if new == 'accepted':
            b.accepted_at = now
        elif new == 'in_progress':
            b.started_at = now
        elif new == 'resolved':
            b.resolved_at = now
        b.save()
        BookingEvent.objects.create(booking=b, status=new, actor=u, note=ser.validated_data.get('note', ''))
        Activity.objects.create(name=f'{_name(u)} moved booking #{b.pk} ({b.service.name}) to {b.get_status_display()}')
        return Response(BookingSerializer(b).data)


class EngineerTrustView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, pk):
        eng = get_object_or_404(EngineerProfile, pk=pk)
        return Response(trust_breakdown(eng))


class CategoriesView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        counts = dict(Service.objects.filter(admin_approved=True).values_list('category').annotate(c=Count('id')))
        return Response([{'key': k, 'label': v, 'count': counts.get(k, 0)} for k, v in CATEGORY_CHOICES])


class AdminStatsView(APIView):
    permission_classes = [IsCustomAdmin]

    def get(self, request):
        now = timezone.now()
        bookings = Booking.objects.all()
        open_q = Q(status__in=['requested', 'accepted', 'in_progress'])
        resolved = bookings.filter(status='resolved').exclude(resolved_at=None)
        res_hours = [(b.resolved_at - b.created_at).total_seconds() / 3600 for b in resolved[:200]]
        days = []
        for i in range(13, -1, -1):
            day = (now - timezone.timedelta(days=i)).date()
            days.append({'date': day.isoformat(), 'bookings': bookings.filter(created_at__date=day).count()})
        engineers = []
        for e in EngineerProfile.objects.select_related('user'):
            open_count = bookings.filter(open_q, service__engineer=e).count()
            engineers.append({'id': e.pk, 'name': _name(e.user), 'open': open_count, **trust_breakdown(e)})
        engineers.sort(key=lambda x: -x['score'])
        by_cat = dict(bookings.values_list('service__category').annotate(c=Count('id')))
        return Response({
            'kpis': {
                'open_bookings': bookings.filter(open_q).count(),
                'sla_breaches': sum(1 for b in bookings.filter(open_q) if b.sla_breached),
                'avg_resolution_hours': round(sum(res_hours) / len(res_hours), 1) if res_hours else None,
                'pending_approvals': Service.objects.filter(admin_approved=False).count(),
                'customers': CustomerProfile.objects.count(),
                'engineers': EngineerProfile.objects.count(),
                'avg_rating': round(Review.objects.aggregate(a=Avg('rating'))['a'] or 0, 1),
            },
            'trend': days,
            'by_category': [{'key': k, 'label': v, 'count': by_cat.get(k, 0)} for k, v in CATEGORY_CHOICES],
            'engineers': engineers,
        })
