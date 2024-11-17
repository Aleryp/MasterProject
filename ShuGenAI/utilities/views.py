from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Count
from features.models import History, Feature
from users.models import User


TEXT_FEATURE_KEYS = ['generate_summary','rewrite_text', 'essay_writer', 'paragraph_writer', 'grammar_checker', 'post_writer', 'document_code']  # Replace with your actual keys
IMAGE_FEATURE_KEYS = ['black_and_white','round_image', "pixelate_image", 'blur_image', 'compress_image', 'remove_background', 'edit_background', 'cut_out_object']  # Replace with your actual keys
FILE_FEATURE_KEYS = ['pdf_to_docx','heif_to_jpg', 'png_to_jpg', 'raw_to_jpg', 'tiff_to_jpg', 'xml_to_json', 'xml_to_json', 'json_to_xml', 'xls_to_csv', 'xls_to_json', 'xls_to_xml', 'docx_to_pdf', 'compress_pdf', 'mp4_to_gif', 'mkv_to_mp4', 'mp4_to_mp3', 'compress_mp4']  # Replace with your actual keys


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
