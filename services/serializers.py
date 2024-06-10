from rest_framework import serializers
from .models import Service
from profiles.serializers import EngineerProfileSerializer, CustomerProfileSerializer


class ServiceSerializer(serializers.ModelSerializer):
    engineer = EngineerProfileSerializer()
    customer = CustomerProfileSerializer(many=True)

    class Meta:
        model = Service
        fields = '__all__'


class ServiceCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['name', 'description', 'price', 'duration']

