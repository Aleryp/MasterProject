from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Card


User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'is_verified', 'first_name',
                  'last_name', 'nickname',  'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class UserBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'is_verified', 'first_name',
                  'last_name', 'nickname', 'is_staff', 'phone_number']


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class PasswordResetVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(write_only=True)


class CardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Card
        fields = ['id', 'card_number', 'card_type', 'expiration_date', 'added_on']
        read_only_fields = ['card_type', 'added_on']

    def validate_card_number(self, value):
        # Ensure card number consists only of digits and has the correct length
        if not value.isdigit() or len(value) != 16:
            raise serializers.ValidationError("Card number must be 16 digits.")
        return value

    def create(self, validated_data):
        card_number = validated_data['card_number']

        # Determine card type based on the card number prefix
        if card_number.startswith('4'):
            validated_data['card_type'] = 'Visa'
        elif card_number.startswith('5'):
            validated_data['card_type'] = 'MasterCard'
        else:
            raise serializers.ValidationError("Invalid card number: must start with 4 for Visa or 5 for MasterCard.")

        return super().create(validated_data)

