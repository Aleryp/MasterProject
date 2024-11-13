import sys

from django.apps import AppConfig


class UtilitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "utilities"

    def ready(self):
        # Check if the server is running (excluding commands like makemigrations and migrate)
        if "runserver" in sys.argv:
            # Import and initialize the ImageAIUtils class only when the server runs
            from utilities.image_ai_utils.utils import ImageAIUtils
            self.image_ai_utils_instance = ImageAIUtils()
