from django.urls import path
from .views import UserFeatureStatsView

urlpatterns = [
    path('stats/', UserFeatureStatsView.as_view(), name='user-feature-stats'),
]
