from rest_framework import serializers

from .models import Booking, BookingEvent


class BookingEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.SerializerMethodField()

    class Meta:
        model = BookingEvent
        fields = ['id', 'status', 'note', 'actor_name', 'created_at']

    def get_actor_name(self, obj):
        return f'{obj.actor.first_name} {obj.actor.last_name}'.strip() if obj.actor else 'System'


class BookingSerializer(serializers.ModelSerializer):
    events = BookingEventSerializer(many=True, read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    service_category = serializers.CharField(source='service.category', read_only=True)
    engineer_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    sla_breached = serializers.BooleanField(read_only=True)

    class Meta:
        model = Booking
        fields = ['id', 'service', 'service_name', 'service_category', 'engineer_name', 'customer_name',
                  'status', 'priority', 'issue', 'triage_summary', 'preferred_time', 'created_at',
                  'accepted_at', 'started_at', 'resolved_at', 'sla_due_at', 'sla_breached', 'events']
        read_only_fields = ['status', 'created_at', 'accepted_at', 'started_at', 'resolved_at', 'sla_due_at']

    def get_engineer_name(self, obj):
        u = obj.service.engineer.user
        return f'{u.first_name} {u.last_name}'.strip() or u.username

    def get_customer_name(self, obj):
        u = obj.customer.user
        return f'{u.first_name} {u.last_name}'.strip() or u.username


class BookingCreateSerializer(serializers.Serializer):
    service = serializers.IntegerField()
    issue = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    triage_summary = serializers.CharField(required=False, allow_blank=True, max_length=4000)
    priority = serializers.ChoiceField(choices=['low', 'normal', 'high', 'critical'], default='normal')
    preferred_time = serializers.DateTimeField(required=False, allow_null=True)


class StatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['accepted', 'in_progress', 'resolved', 'cancelled'])
    note = serializers.CharField(required=False, allow_blank=True, max_length=2000)
