from rest_framework import serializers
from .models import Review
from profiles.serializers import CustomerProfileSerializer
from services.serializers import ServiceSerializer
from rest_framework.serializers import StringRelatedField


class ReviewSerializer(serializers.ModelSerializer):
    user = CustomerProfileSerializer(read_only=True)
    service = ServiceSerializer(read_only=True)
    customer = StringRelatedField()

    class Meta:
        model = Review
        fields = '__all__'


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['rating', 'comment']
