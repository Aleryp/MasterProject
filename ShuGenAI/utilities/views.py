from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count
from features.models import History, Feature
from users.models import User


TEXT_FEATURE_KEYS = ['generate_summary',]  # Replace with your actual keys
IMAGE_FEATURE_KEYS = ['black_and_white',]  # Replace with your actual keys
FILE_FEATURE_KEYS = ['pdf_to_docx',]  # Replace with your actual keys



class UserFeatureStatsView(APIView):
    permission_classes = [AllowAny]  # Ensure user is authenticated

    def get(self, request):
        # Count of users
        user_count = User.objects.count()

        # Count of used features
        total_feature_count = Feature.objects.count()

        # Count used text features
        text_usage_count = History.objects.filter(
            feature__key__in=TEXT_FEATURE_KEYS
        ).count()

        # Count used image features
        image_usage_count = History.objects.filter(
            feature__key__in=IMAGE_FEATURE_KEYS
        ).count()

        # Count used file features
        file_usage_count = History.objects.filter(
            feature__key__in=FILE_FEATURE_KEYS
        ).count()

        # Prepare the response data
        response_data = {
            'user_count': user_count,
            'text_feature_count': text_usage_count,
            'image_feature_count': image_usage_count,
            'file_feature_count': file_usage_count,
            'total_feature_count': total_feature_count,
        }

        return Response(response_data)
