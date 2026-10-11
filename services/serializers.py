from rest_framework import serializers
from .models import Service
from profiles.serializers import EngineerProfileSerializer, CustomerProfileSerializer


class ServiceSerializer(serializers.ModelSerializer):
    engineer = EngineerProfileSerializer()
    customer = CustomerProfileSerializer(many=True)
    category_label = serializers.CharField(source='get_category_display', read_only=True)
    avg_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    trust = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = '__all__'

    def get_avg_rating(self, obj):
        vals = [r.rating for r in obj.reviews.all()]
        return round(sum(vals) / len(vals), 1) if vals else None

    def get_review_count(self, obj):
        return len(obj.reviews.all())

    def get_trust(self, obj):
        from bookings.trust import trust_breakdown
        cache = self.context.setdefault('_trust', {}) if hasattr(self, 'context') and isinstance(self.context, dict) else {}
        key = obj.engineer_id
        if key not in cache:
            cache[key] = trust_breakdown(obj.engineer)
        return cache[key]


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'duration', 'category', 'sla_hours', 'is_remote']

