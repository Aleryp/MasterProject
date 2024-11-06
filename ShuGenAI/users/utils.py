import random
from django.core.mail import send_mail
from django.conf import settings

def generate_verification_code():
    return str(random.randint(100000, 999999))

def send_verification_email(user, code):
    subject = 'Verify your email'
    message = f'Your verification code is {code}'
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])

def send_password_reset_code(user, code):
    subject = 'Password Reset Code'
    message = f'Your password reset code is {code}'
    send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
