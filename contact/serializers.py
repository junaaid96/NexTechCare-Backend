from rest_framework import serializers
from .models import ContactText


class ContactTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactText
        fields = '__all__'
