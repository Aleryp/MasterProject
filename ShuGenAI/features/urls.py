from django.urls import path
from .views import (FeatureListView, PlansView,
                    CreateSubscriptionView, UserSubscriptionView, process_feature,
                    UserHistoryView, RecentFeaturesView)

urlpatterns = [
    path('user-history/', UserHistoryView.as_view(), name='user-history'),
    path('features/recent/', RecentFeaturesView.as_view(), name='recent-features'),
    path('features/', FeatureListView.as_view(), name='feature-list'),
    path('plans/', PlansView.as_view(), name='plans-list'),
    path('subscriptions/', CreateSubscriptionView.as_view(), name='create-subscription'),
    path('subscriptions/user/', UserSubscriptionView.as_view(), name='user-subscription'),
    path('<str:feature_key>/', process_feature, name='process-feature'),
]