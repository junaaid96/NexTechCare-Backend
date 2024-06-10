from rest_framework import serializers
from .models import User, AdminProfile, CustomerProfile, EngineerProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name',
                  'email', 'user_type', 'is_active']


class UserRegistrationSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    email = serializers.EmailField(required=True)
    confirm_password = serializers.CharField(write_only=True)
    user_type = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name',
                  'email', 'password', 'confirm_password', 'user_type']
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def validate(self, data):
        errors = {}

        password = data.get('password')
        confirm_password = data.pop('confirm_password', None)
        if password != confirm_password:
            errors['password'] = 'Passwords must match!'

        user_type = data.get('user_type')
        if user_type not in ['C', 'E']:
            errors['user_type'] = 'User type must be either Customer or Engineer.'

        email = data.get('email')
        if email and User.objects.filter(email=email).exists():
            errors['email'] = 'Email already exists!'

        if errors:
            raise serializers.ValidationError(errors)

        return data

    # def to_internal_value(self, data):
    #     try:
    #         return super().to_internal_value(data)
    #     except serializers.ValidationError as e:
    #         raise serializers.ValidationError({'errors': e.detail})

    def create(self, validated_data):
        user_type = validated_data.get('user_type')
        user = User.objects.create_user(**validated_data)

        if user_type == 'C':
            CustomerProfile.objects.create(user=user)
        elif user_type == 'E':
            EngineerProfile.objects.create(user=user)

        return user


class AdminProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = AdminProfile
        fields = ['user', 'phone', 'address', 'task', 'image']


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = CustomerProfile
        fields = ['user', 'phone', 'address', 'occupation', 'image']


class CustomerProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerProfile
        fields = ['phone', 'address', 'occupation', 'image']

    def update(self, instance, validated_data):
        instance.phone = validated_data.get('phone', instance.phone)
        instance.address = validated_data.get('address', instance.address)
        instance.occupation = validated_data.get(
            'occupation', instance.occupation)
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        return instance


class EngineerProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = EngineerProfile
        fields = ['user', 'phone', 'address', 'skills', 'experience', 'image']


class EngineerProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EngineerProfile
        fields = ['phone', 'address', 'skills', 'experience', 'image']

    def update(self, instance, validated_data):
        instance.phone = validated_data.get('phone', instance.phone)
        instance.address = validated_data.get('address', instance.address)
        instance.skills = validated_data.get('skills', instance.skills)
        instance.experience = validated_data.get(
            'experience', instance.experience)
        instance.image = validated_data.get('image', instance.image)
        instance.save()
        return instance


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()
