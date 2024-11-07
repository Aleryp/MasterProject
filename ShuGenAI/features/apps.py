import os

from django.apps import AppConfig
from django.conf import settings


class FeaturesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "features"

    def ready(self):
        import features.signals
        directory_path = os.path.join(settings.BASE_DIR, '../tmp')
        # Create the directory if it does not exist
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
