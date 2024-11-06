from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
from .serializers import (
    UserRegistrationSerializer, EmailVerificationSerializer,
    PasswordResetSerializer, PasswordResetVerificationSerializer, ResendVerificationSerializer,
    PasswordChangeSerializer, CardSerializer
)
from .utils import generate_verification_code, send_verification_email, send_password_reset_code
from django.contrib.auth import get_user_model
from .models import Card
from rest_framework import status


User = get_user_model()

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.initial_data.get('email'):
            users = User.objects.filter(email=serializer.initial_data.get('email')).exists()
            if users:
                user = User.objects.get(email=serializer.initial_data.get('email'))
                if user and not user.is_verified:
                    code = generate_verification_code()
                    user.verification_code = code
                    user.save()
                    send_verification_email(user, code)
                    return Response({'status': 'Already registered. Sending code again.'},
                                    status=205)
        if serializer.is_valid():
            # Create the user with the hashed password
            user = serializer.save()
            user.set_password(serializer.validated_data['password'])
            code = generate_verification_code()
            user.verification_code = code
            user.save()
            send_verification_email(user, code)
            return Response({'status': 'Registration successful. Check your email for the code.'})
        return Response(serializer.errors, status=400)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            # Verify the code against stored code
            user = User.objects.get(email=serializer.validated_data['email'])
            if serializer.validated_data['code'] == user.verification_code:
                user.verification_code = None
                user.is_verified = True
                user.save()
                return Response({'status': 'Email verified'})
        return Response(serializer.errors, status=400)


class ResendVerificationEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = User.objects.get(email=serializer.validated_data['email'])
            code = generate_verification_code()
            user.verification_code = code
            user.save()
            send_verification_email(user, code)
            # Save the code to user profile or model
            return Response({'status': 'Code send. Check your email for the code.'})
        return Response(serializer.errors, status=400)

class PasswordResetView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            code = generate_verification_code()
            user = User.objects.get(email=serializer.validated_data['email'])
            user.verification_code = code
            user.save()
            send_password_reset_code(user, code)
            return Response({'status': 'Password reset code sent'})
        return Response(serializer.errors, status=400)

class PasswordResetVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetVerificationSerializer(data=request.data)
        if serializer.is_valid():
            # Verify code and update password
            user = User.objects.get(email=serializer.validated_data['email'])
            if serializer.validated_data['code'] == user.verification_code:
                user.verification_code = None
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'status': 'Password updated'})
        return Response(serializer.errors, status=400)


class PasswordChangeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data)

        if serializer.is_valid():
            user = request.user
            old_password = serializer.validated_data['old_password']
            new_password = serializer.validated_data['new_password']

            # Verify the old password
            if not check_password(old_password, user.password):
                return Response({'error': 'Old password is incorrect'}, status=status.HTTP_400_BAD_REQUEST)

            # Set the new password
            user.set_password(new_password)
            user.save()
            return Response({'status': 'Password updated successfully'}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardListCreateView(generics.ListCreateAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class CardDeleteView(generics.DestroyAPIView):
    serializer_class = CardSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Card.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

