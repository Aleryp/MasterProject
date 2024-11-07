from collections import OrderedDict
from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Feature, History, Plans, Subscription
from django.contrib.auth import get_user_model
from .serializers import (FeatureSerializer, HistorySerializer,
                          PlansSerializer, SubscriptionSerializer, FeatureKeySerializer)
from django.http import JsonResponse
from django.utils import timezone
from utilities import file_utils, text_utils, image_utils


User = get_user_model()

class FeatureListView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        features = Feature.objects.all()  # Fetch all Feature instances
        serializer = FeatureSerializer(features, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class PlansView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        # Retrieve all plans with their features
        plans = Plans.objects.prefetch_related('features').all()
        serializer = PlansSerializer(plans, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CreateSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_key = request.data.get('plan_key')
        duration = request.data.get('duration', 30)  # default duration is 30 days

        try:
            plan = Plans.objects.get(key=plan_key)
        except Plans.DoesNotExist:
            return Response({"error": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create or update the subscription
        if Subscription.objects.filter(user=request.user, plan=plan).exists():
            return Response({"error": "Subscription already exists"}, status=status.HTTP_400_BAD_REQUEST)
        elif Subscription.objects.filter(user=request.user).exists():
            Subscription.objects.filter(user=request.user).update(plan=plan,
                                                                  end_date=timezone.now() + timedelta(days=int(duration)))
            subscription = Subscription.objects.get(user=request.user, plan=plan)
        else:
            subscription = Subscription.objects.create(
                user=request.user,
                plan=plan,
                end_date=timezone.now() + timedelta(days=int(duration))
            )

        serializer = SubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserSubscriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Retrieve the subscription for the authenticated user
        try:
            subscription = Subscription.objects.get(user=request.user)
            serializer = SubscriptionSerializer(subscription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Subscription.DoesNotExist:
            return Response({"error": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)

    def delete(self, request):
        # Delete the subscription for the authenticated user
        try:
            subscription = Subscription.objects.get(user=request.user)
            subscription.delete()
            return Response({"message": "Subscription cancelled successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Subscription.DoesNotExist:
            return Response({"error": "No active subscription found."}, status=status.HTTP_404_NOT_FOUND)


class UserHistoryView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def get(self, request):
        # Filter history for the authenticated user
        user_history = History.objects.filter(user=request.user)

        # Serialize the user's history
        serializer = HistorySerializer(user_history, many=True, context={'request': request})

        # Return the serialized data
        return Response(serializer.data)



class RecentFeaturesView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure user is authenticated

    def get(self, request):
        # Get the user's history, ordered by most recent date
        recent_features = (
            History.objects.filter(user=request.user)
            .select_related('feature')  # Optimize query by selecting related feature
            .order_by('-date')
        )

        # Use an ordered dict to keep unique features while preserving order
        unique_features = OrderedDict()
        for history in recent_features:
            if history.feature_id not in unique_features:
                unique_features[history.feature_id] = history.feature

            # Stop if we have 5 unique features
            if len(unique_features) == 5:
                break

        # Serialize the unique features
        serializer = FeatureKeySerializer(unique_features.values(), many=True)

        # Return the serialized data
        return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def process_feature(request, feature_key):
    # Step 1: Verify if the feature exists
    feature = get_object_or_404(Feature, key=feature_key)

    # Step 2: Check if the user has an active subscription with a plan that includes this feature
    if not request.user.is_authenticated:
        return Response({"status": "error", "message": "User is not authenticated"}, status=401)
    user_subscriptions = Subscription.objects.filter(
        user=request.user,
        end_date__gt=timezone.now()  # Subscription must be active
    ).select_related('plan').prefetch_related('plan__features')

    # Step 3: Verify if any subscription includes the feature
    has_access = any(feature in subscription.plan.features.all() for subscription in user_subscriptions)

    if has_access:
        # Proceed with your additional logic if feature access is confirmed
        return determine_feature(request, feature_key)
    else:
        return Response({"status": "error", "message": "Access denied to this feature."}, status=403)


def determine_feature(request, feature_key):
    FEATURES_DICT = {"black_and_white": image_utils.convert_image_to_bw,
                     "round_image": image_utils.convert_image_to_round,
                     "pixelate_image": image_utils.convert_image_to_pixelated,
                     "blur_image": image_utils.convert_image_to_blurred,
                     "compress_image": image_utils.compress_image,
                     "heif_to_jpg": image_utils.convert_heic_to_jpg,
                     "png_to_jpg": image_utils.convert_png_to_jpg,
                     "raw_to_jpg": image_utils.convert_raw_to_jpg,
                     "tiff_to_jpg": image_utils.convert_tiff_to_jpg,
                     "xml_to_json": file_utils.convert_xml_to_json,
                     "json_to_xml": file_utils.convert_json_to_xml,
                     "xml_to_csv": file_utils.convert_xml_to_csv,
                     "json_to_csv": file_utils.convert_json_to_csv,
                     "xls_to_csv": file_utils.convert_xls_to_csv,
                     "xls_to_json": file_utils.convert_xls_to_json,
                     "xls_to_xml": file_utils.convert_xls_to_xml,
                     "pdf_to_docx": file_utils.convert_pdf_to_docx,
                     "docx_to_pdf": file_utils.convert_docx_to_pdf,
                     "compress_pdf": file_utils.pdf_compression,
                     "mp4_to_gif": file_utils.convert_mp4_to_gif,
                     "mkv_to_mp4": file_utils.convert_mkv_to_mp4,
                     "mp4_to_mp3": file_utils.convert_mp4_to_mp3,
                     "compress_mp4": file_utils.compress_mp4,
                     "generate_summary": text_utils.generate_summary,
                     "rewrite_text": text_utils.rewrite_text,
                     "essay_writer": text_utils.essay_writer,
                     "paragraph_writer": text_utils.paragraph_writer,
                     "grammar_checker": text_utils.grammar_checker,
                     "post_writer": text_utils.post_writer,
                     "document_code": text_utils.document_code,
                     }

    return FEATURES_DICT[feature_key](request, feature_key)