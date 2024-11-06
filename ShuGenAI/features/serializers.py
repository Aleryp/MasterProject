from rest_framework import serializers
from .models import Feature, History, Plans, Subscription
from django.conf import settings


class FeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['id', 'key', 'used_count']


class HistorySerializer(serializers.ModelSerializer):
    feature = FeatureSerializer()
    file = serializers.SerializerMethodField()  # Use `SerializerMethodField` for full URL

    class Meta:
        model = History
        fields = ['id', 'user', 'date', 'feature', 'file']

    def get_file(self, obj):
        request = self.context.get('request')
        if request is not None:
            return request.build_absolute_uri(obj.file.url)  # Generates absolute URL
        return f"{settings.MEDIA_URL}{obj.file}"  # Builds full URL if no request


class PlansSerializer(serializers.ModelSerializer):
    features = FeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Plans
        fields = ['id', 'key', 'features']

class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['id', 'user', 'plan', 'start_date', 'end_date']


class FeatureKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = Feature
        fields = ['key']  # Only serialize the feature key
