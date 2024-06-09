from rest_framework import serializers
from .models import Review
from profiles.serializers import CustomerProfileSerializer
from services.serializers import ServiceSerializer


class ReviewSerializer(serializers.ModelSerializer):
    user = CustomerProfileSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)

    class Meta:
        model = Review
        fields = '__all__'


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
