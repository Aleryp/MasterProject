from django.apps import AppConfig


class UtilitiesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "utilities"

    def ready(self):
        # Import and initialize the ImageAIUtils class when the app is ready
        from image_ai_utils.utils import ImageAIUtils
        self.image_ai_utils_instance = ImageAIUtils()
