from rest_framework import serializers
from .models import Service
from profiles.models import EngineerProfile, CustomerProfile
from profiles.serializers import EngineerProfileSerializer, CustomerProfileSerializer


class ServiceSerializer(serializers.ModelSerializer):
    engineer = EngineerProfileSerializer()
    customer = CustomerProfileSerializer(many=True)

    class Meta:
        model = Service
        fields = '__all__'


class ServiceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

    def create(self, validated_data):
        engineer_data = validated_data.pop('engineer')
        engineer = EngineerProfile.objects.get(**engineer_data)
        service = Service.objects.create(engineer=engineer, **validated_data)
        return service


class ServiceUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

    def update(self, instance, validated_data):
        engineer_data = validated_data.pop('engineer')
        engineer = EngineerProfile.objects.get(**engineer_data)
        instance.engineer = engineer
        instance.name = validated_data.get('name', instance.name)
        instance.description = validated_data.get(
            'description', instance.description)
        instance.price = validated_data.get('price', instance.price)
        instance.duration = validated_data.get('duration', instance.duration)
        instance.review_text = validated_data.get(
            'review_text', instance.review_text)
        instance.admin_approved = validated_data.get(
            'admin_approved', instance.admin_approved)
        instance.save()
        return instance
