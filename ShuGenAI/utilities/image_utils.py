import base64

import pillow_heif
import rawpy
from django.core.files.base import ContentFile
from django.http import JsonResponse
from PIL import Image, ImageDraw, ImageFilter
from io import BytesIO
from django.contrib.staticfiles import finders
from rest_framework import status
from features.models import History, Feature
from features.serializers import HistorySerializer
from django.apps import apps
from django.core.files.storage import FileSystemStorage
import pickle
import numpy as np


BACKGROUNDS_DICT = {
    1: finders.find('backgrounds/city.jpg'),
    2: finders.find('backgrounds/beach.jpg'),
    3: finders.find('backgrounds/desert.jpg'),
    4: finders.find('backgrounds/field.jpg'),
    5: finders.find('backgrounds/forest_autumn.jpg'),
    6: finders.find('backgrounds/forest.jpg'),
    7: finders.find('backgrounds/mountains.jpg'),
    8: finders.find('backgrounds/snow_mountains.jpg'),
    9: finders.find('backgrounds/office.jpg'),
    10: finders.find('backgrounds/underwater.jpg')
}


def convert_image_to_bw(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_image = request.FILES["file"]
        # Open the image and convert it to black and white
        image = Image.open(uploaded_image)
        bw_image = image.convert("L")
        # Save the black and white image to a BytesIO buffer
        buffer = BytesIO()
        bw_image.save(buffer, format="JPEG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="bw_image.jpg")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None # Feature ID should be provided in the request
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)


def convert_image_to_round(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_image = request.FILES["file"]
        # Open the image and ensure it's in RGBA mode (supports transparency)
        image = Image.open(uploaded_image).convert("RGBA")
        # Create a mask to make the image round
        size = min(image.size)  # Ensure the mask is square and covers the minimum dimension of the image
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        # Crop and apply the mask to the image
        cropped_image = image.crop((0, 0, size, size))
        cropped_image.putalpha(mask)
        # Save the round image to a BytesIO buffer as a PNG (supports transparency)
        buffer = BytesIO()
        cropped_image.save(buffer, format="PNG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="round_image.png")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)
def convert_image_to_pixelated(request, feature_key, pixel_size=5):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_image = request.FILES["file"]
        # Open the image
        image = Image.open(uploaded_image).convert("RGBA")
        # Pixelate the image
        width, height = image.size
        small_image = image.resize(
            (width // pixel_size, height // pixel_size),
            resample=Image.BILINEAR
        )
        pixelated_image = small_image.resize((width, height), Image.NEAREST).convert("RGB")
        # Save the pixelated image to a BytesIO buffer
        buffer = BytesIO()
        pixelated_image.save(buffer, format="JPEG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="pixelated_image.jpg")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)

def convert_image_to_blurred(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        # Get blur intensity from request (default to 5 if not provided)
        blur_intensity = int(request.POST.get("blur_intensity", 5))
        uploaded_image = request.FILES["file"]
        # Open the image
        image = Image.open(uploaded_image)
        # Apply Gaussian blur to the image
        blurred_image = image.filter(ImageFilter.GaussianBlur(blur_intensity))
        # Save the blurred image to a BytesIO buffer
        buffer = BytesIO()
        blurred_image.save(buffer, format="JPEG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="blurred_image.jpg")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)

def compress_image(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        # Get compression quality from request (default to 70 if not provided)
        compression_quality = int(request.POST.get("compression_quality", 70))
        # Ensure the compression quality is between 1 and 100
        compression_quality = max(1, min(compression_quality, 100))
        uploaded_image = request.FILES["file"]
        # Open the image
        image = Image.open(uploaded_image)
        # Save the image to a BytesIO buffer with the specified quality
        buffer = BytesIO()
        if image.mode in ("RGBA", "LA"):
            image = image.convert("RGB")
        image.save(buffer, format="JPEG", quality=compression_quality)
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="compressed_image.jpg")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)


def convert_heic_to_jpg(request, feature_key):
    pillow_heif.register_heif_opener()
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_image = request.FILES["file"]
        # Open the HEIC image
        image = Image.open(uploaded_image)
        # Ensure image is loaded in RGB mode for compatibility with JPEG format
        if image.mode in ("RGBA", "LA"):
            image = image.convert("RGB")
        # Save the image as JPG to a BytesIO buffer
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="heic_image.jpg")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)


def convert_png_to_jpg(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_image = request.FILES["file"]
        # Open the PNG image
        image = Image.open(uploaded_image)
        # Ensure image is loaded in RGB mode for compatibility with JPEG format
        if image.mode in ("RGBA", "LA"):
            # Create a white background and paste the PNG onto it
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])  # Use alpha channel as mask
            image = background
        elif image.mode != "RGB":
            image = image.convert("RGB")
        # Save the image as JPG to a BytesIO buffer
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="png_image.jpg")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)

def convert_raw_to_jpg(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_image = request.FILES["file"]
        # Use rawpy to read the RAW image
        with rawpy.imread(uploaded_image) as raw:
            rgb_image = raw.postprocess()
        # Convert the numpy array (RGB image) to a Pillow Image
        image = Image.fromarray(rgb_image)
        # Save the image as JPG to a BytesIO buffer
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="raw_image.jpg")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)

def convert_tiff_to_jpg(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_image = request.FILES["file"]
        # Open the TIFF image
        image = Image.open(uploaded_image)
        # Ensure image is in RGB mode for compatibility with JPEG format
        if image.mode != "RGB":
            image = image.convert("RGB")
        # Save the image as JPG to a BytesIO buffer
        buffer = BytesIO()
        image.save(buffer, format="JPEG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="tiff_image.jpg")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)


def remove_background(request, feature_key):
    image_ai_utils = apps.get_app_config('utilities').image_ai_utils_instance
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_image = request.FILES["file"]
        input_image = Image.open(uploaded_image)
        _, predictions = image_ai_utils.infer_image(input_image)
        image = image_ai_utils.remove_background(input_image, predictions)
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="remove_background.png")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)

def edit_background(request, feature_key):
    image_ai_utils = apps.get_app_config('utilities').image_ai_utils_instance
    if request.method == "POST" and request.FILES.get("file") and request.POST.get("background"):
        uploaded_image = request.FILES["file"]
        background_image = BACKGROUNDS_DICT[int(request.POST["background"])]
        input_image = Image.open(uploaded_image)
        input_background = Image.open(background_image)

        _, predictions = image_ai_utils.infer_image(input_image)
        image = image_ai_utils.edit_background(input_image, input_background, predictions)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="edited_background.png")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)


def pick_up_object(request, feature_key):
    image_ai_utils = apps.get_app_config('utilities').image_ai_utils_instance

    if request.method == "POST" and request.FILES.get("file") and not request.POST.get('objects'):
        uploaded_image = request.FILES["file"]
        input_image = Image.open(uploaded_image)
        language = request.POST.get('language', "en")
        # Get predictions and segmented image
        segmented_image, predictions = image_ai_utils.infer_image(input_image, language)

        # Serialize predictions
        serialized_predictions = pickle.dumps(predictions)

        # Encode the serialized data as base64
        encoded_predictions = base64.b64encode(serialized_predictions).decode('utf-8')

        # Save the encoded string in the session
        request.session['predictions'] = encoded_predictions

        # Save the segmented image to the file system
        buffer = BytesIO()
        segmented_image.save(buffer, format="PNG")
        buffer.seek(0)
        fs = FileSystemStorage()
        image_path = fs.save('segmented_images/segmented_image.png', ContentFile(buffer.getvalue()))

        return JsonResponse({
            'segmented_image_url': request.build_absolute_uri(fs.url(image_path)),
            'objects': list(predictions.keys())
        })

    elif request.method == "POST" and request.FILES.get("file") and request.POST.get('objects'):
        uploaded_image = request.FILES["file"]
        input_image = Image.open(uploaded_image)
        objects_str = request.POST.get('objects')

        if ',' in objects_str:
            objects_list = objects_str.split(',')
        else:
            objects_list = [objects_str]

        # Retrieve the base64-encoded string from the session
        encoded_predictions = request.session.get('predictions', None)
        predictions = {}
        if encoded_predictions:
            # Decode the base64 string back to bytes
            serialized_predictions = base64.b64decode(encoded_predictions.encode('utf-8'))

            # Deserialize the predictions
            predictions = pickle.loads(serialized_predictions)

        # Process image with the picked-up objects
        image = image_ai_utils.pick_up_object(input_image, objects_list, predictions)

        # Convert image to buffer for saving
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        # Create a ContentFile for saving the image
        image_file = ContentFile(buffer.getvalue(), name="picked.png")

        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()

        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)

        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})

        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)

def cut_out_object(request, feature_key):
    image_ai_utils = apps.get_app_config('utilities').image_ai_utils_instance
    if request.method == "POST" and request.FILES.get("file") and not request.POST.get('objects'):
        uploaded_image = request.FILES["file"]
        input_image = Image.open(uploaded_image)
        language = request.POST.get('language', "en")
        # Get predictions and segmented image
        segmented_image, predictions = image_ai_utils.infer_image(input_image, language)
        # Serialize predictions
        serialized_predictions = pickle.dumps(predictions)

        # Encode the serialized data as base64
        encoded_predictions = base64.b64encode(serialized_predictions).decode('utf-8')

        # Save the encoded string in the session
        request.session['predictions'] = encoded_predictions

        # Save the segmented image to the file system
        buffer = BytesIO()
        segmented_image.save(buffer, format="PNG")
        buffer.seek(0)
        fs = FileSystemStorage()
        image_path = fs.save('segmented_images/segmented_image.png', ContentFile(buffer.getvalue()))

        return JsonResponse({
            'segmented_image_url': request.build_absolute_uri(fs.url(image_path)),
            'objects': list(predictions.keys())
        })
    if request.method == "POST" and request.FILES.get("file") and request.POST.get('objects'):
        uploaded_image = request.FILES["file"]
        input_image = Image.open(uploaded_image)
        objects_str = request.POST.get('objects')
        if ',' in objects_str:
            objects_list = objects_str.split(',')
        else:
            objects_list = [objects_str]
        # Retrieve the base64-encoded string from the session
        encoded_predictions = request.session.get('predictions', None)
        predictions = {}
        if encoded_predictions:
            # Decode the base64 string back to bytes
            serialized_predictions = base64.b64decode(encoded_predictions.encode('utf-8'))

            # Deserialize the predictions
            predictions = pickle.loads(serialized_predictions)

        image = image_ai_utils.cut_out_object(input_image, objects_list, predictions)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
        # Create a ContentFile for saving to the FileField
        image_file = ContentFile(buffer.getvalue(), name="cut.png")
        # Get the user and feature, assuming the user is authenticated
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        feature.used_count += 1
        feature.save()
        # Create and save the History instance
        history = History.objects.create(user=user, file=image_file, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no image provided"}, status=status.HTTP_400_BAD_REQUEST)