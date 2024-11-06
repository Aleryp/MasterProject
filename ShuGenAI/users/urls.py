from django.urls import path
from .views import (RegisterView, VerifyEmailView, PasswordResetView,
                    PasswordResetVerificationView, ResendVerificationEmailView,
                    PasswordChangeView, CardListCreateView, CardDeleteView)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('password-change/', PasswordChangeView.as_view(), name='password-change'),
    path('password-reset/', PasswordResetView.as_view(), name='password-reset'),
    path('password-reset-verification/', PasswordResetVerificationView.as_view(), name='password-change'),
    path('resend-verification/', ResendVerificationEmailView.as_view(), name='resend-verification'),
    path('cards/', CardListCreateView.as_view(), name='card-list-create'),
    path('cards/<int:pk>/', CardDeleteView.as_view(), name='card-delete'),
]