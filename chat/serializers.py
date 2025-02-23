from rest_framework import serializers
from .models import *
from django.core.validators import validate_email, EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'}, min_length=8)

    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'password', 'is_active', 'is_staff', 'is_superuser', 'status', 'date_joined',
                  'last_login']

    def validate_email(self, value):
        """Validate the email field using Django's EmailValidator."""
        email_validator = EmailValidator()

        try:
            email_validator(value)
        except ValidationError as err:
            raise serializers.ValidationError("Invalid email address.")

        return value

    def validate(self, data):
        if User.objects.filter(email=data.get('email')).exists():
            raise serializers.ValidationError('User Already Exists.')
        return data

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        request = self.context.get('request')
        user = authenticate(request, email=email, password=password)

        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        return {'user': user}


class PrivateChatSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrivateChat
        fields = '__all__'

class MessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.username')
    receiver = serializers.ReadOnlyField(source='receiver.username')

    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'timestamp', 'seen']