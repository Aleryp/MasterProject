from django.core.files.base import ContentFile
from django.http import JsonResponse
from rest_framework import status
from features.models import History, Feature
from features.serializers import HistorySerializer
from django.conf import settings
import os
from openai import OpenAI

api_key = os.environ.get("AI_API_KEY", "api_key")
base_url = "https://api.aimlapi.com/v1"
client = OpenAI(api_key=api_key, base_url=base_url)


def process_file_with_openai(text):
    response_content = None
    try:
        # Step 1: Define prompts
        system_prompt = """You are a text analizer."""
        user_prompt = f"Give a short summary of file using provided instructions. Limit your response to 50 words. Process this text: {text}"
        # Step 2: Prepare the API call to OpenAI with the uploaded file
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify your model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=256,
        )
        # Step 3: Get the response content
        if response.choices:
            response_content = response.choices[0].message.content
        # Step 4: Delete the uploaded file after processing
        return response_content if response_content else "No content generated."
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def generate_summary(request, feature_key):
    if request.method == "POST":
        text = request.POST.get('text')
        if not text:
            return JsonResponse({"error": "No input text provided"}, status=status.HTTP_400_BAD_REQUEST)
        if settings.USE_MOCK_OUTPUT:
            generated_text = f"This is a mock generated text for demonstration purposes. Text: {text}"
        else:
            response = process_file_with_openai(text)
            if isinstance(response, JsonResponse):
                return response
            else:
                generated_text = response
        # Save the generated text to a temporary .txt file
        text_file_name = "generated_text.txt"
        text_file_path = f"./tmp/{text_file_name}"

        with open(text_file_path, 'w', encoding="utf-8") as text_file:
            text_file.write(generated_text)
        # Read the .txt file to save to the History model
        with open(text_file_path, 'rb') as txt_file:
            txt_content = ContentFile(txt_file.read(), name=text_file_name)
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=txt_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(text_file_path)
        # Add the generated text to the response
        response_data = serializer.data
        response_data["text"] = generated_text
        # Return the serialized data with the generated text
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)


def rewrite_text_with_openai(text):
    response_content = None
    try:
        # Step 1: Define prompts
        system_prompt = """You will be provided with a text.
                                You should rewrite this text so that it is clearer and easier to read."""
        user_prompt = f"This is text to be rewriten: {text}"
        # Step 2: Prepare the API call to OpenAI with the uploaded file
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify your model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=256,
        )
        # Step 3: Get the response content
        if response.choices:
            response_content = response.choices[0].message.content

        return response_content if response_content else "No content generated."
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def rewrite_text(request, feature_key):
    if request.method == "POST":
        text = request.POST.get('text')
        if not text:
            return JsonResponse({"error": "No input text provided"}, status=status.HTTP_400_BAD_REQUEST)
        if settings.USE_MOCK_OUTPUT:
            generated_text = f"This is mocked rewritten text for demonstration. \nInput text: {text}"
        else:
            response = rewrite_text_with_openai(text)
            if isinstance(response, JsonResponse):
                return response
            else:
                generated_text = response
        # Save the generated text to a temporary .txt file
        text_file_name = "generated_text.txt"
        text_file_path = f"./tmp/{text_file_name}"

        with open(text_file_path, 'w', encoding="utf-8") as text_file:
            text_file.write(generated_text)
        # Read the .txt file to save to the History model
        with open(text_file_path, 'rb') as txt_file:
            txt_content = ContentFile(txt_file.read(), name=text_file_name)
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=txt_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(text_file_path)
        # Add the generated text to the response
        response_data = serializer.data
        response_data["text"] = generated_text
        # Return the serialized data with the generated text
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)


def write_essay_with_openai(text):
    response_content = None
    try:
        # Step 1: Define prompts
        system_prompt = """You are a writer.
                                You should write a medium sized essay on given topic. Limit Your response to 200 words."""
        user_prompt = f"This is topic for the essay: {text}"
        # Step 2: Prepare the API call to OpenAI with the uploaded file
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify your model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=256,
        )
        # Step 3: Get the response content
        if response.choices:
            response_content = response.choices[0].message.content

        return response_content if response_content else "No content generated."
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def essay_writer(request, feature_key):
    if request.method == "POST":
        text = request.POST.get('text')
        if not text:
            return JsonResponse({"error": "No input text provided"}, status=status.HTTP_400_BAD_REQUEST)
        if settings.USE_MOCK_OUTPUT:
            generated_text = f"This is mocked essay writer for demonstration. \nInput text: {text}"
        else:
            response = write_essay_with_openai(text)
            if isinstance(response, JsonResponse):
                return response
            else:
                generated_text = response
        # Save the generated text to a temporary .txt file
        text_file_name = "generated_text.txt"
        text_file_path = f"./tmp/{text_file_name}"

        with open(text_file_path, 'w', encoding="utf-8") as text_file:
            text_file.write(generated_text)
        # Read the .txt file to save to the History model
        with open(text_file_path, 'rb') as txt_file:
            txt_content = ContentFile(txt_file.read(), name=text_file_name)
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=txt_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(text_file_path)
        # Add the generated text to the response
        response_data = serializer.data
        response_data["text"] = generated_text
        # Return the serialized data with the generated text
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)

def write_paragraph_with_openai(text):
    response_content = None
    try:
        # Step 1: Define prompts
        system_prompt = """You are a writer.
                                You should write a short paragraph on given topic. Limit your response to 100 words."""
        user_prompt = f"This is topic for the paragraph: {text}"
        # Step 2: Prepare the API call to OpenAI with the uploaded file
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify your model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=256,
        )
        # Step 3: Get the response content
        if response.choices:
            response_content = response.choices[0].message.content

        return response_content if response_content else "No content generated."
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def paragraph_writer(request, feature_key):
    if request.method == "POST":
        text = request.POST.get('text')
        if not text:
            return JsonResponse({"error": "No input text provided"}, status=status.HTTP_400_BAD_REQUEST)
        if settings.USE_MOCK_OUTPUT:
            generated_text = f"This is mocked paragraph writer for demonstration. \nInput text: {text}"
        else:
            response = write_paragraph_with_openai(text)
            if isinstance(response, JsonResponse):
                return response
            else:
                generated_text = response
        # Save the generated text to a temporary .txt file
        text_file_name = "generated_text.txt"
        text_file_path = f"./tmp/{text_file_name}"

        with open(text_file_path, 'w', encoding="utf-8") as text_file:
            text_file.write(generated_text)
        # Read the .txt file to save to the History model
        with open(text_file_path, 'rb') as txt_file:
            txt_content = ContentFile(txt_file.read(), name=text_file_name)
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=txt_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(text_file_path)
        # Add the generated text to the response
        response_data = serializer.data
        response_data["text"] = generated_text
        # Return the serialized data with the generated text
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)

def check_grammar_with_openai(text):
    response_content = None
    try:
        # Step 1: Define prompts
        system_prompt = """You are a teacher.Rewrite this text with all grammatical rules.Provide short summary of text."""
        user_prompt = f"This is text: {text}"
        # Step 2: Prepare the API call to OpenAI with the uploaded file
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify your model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=256,
        )
        # Step 3: Get the response content
        if response.choices:
            response_content = response.choices[0].message.content

        return response_content if response_content else "No content generated."
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def grammar_checker(request, feature_key):
    if request.method == "POST":
        text = request.POST.get('text')
        if not text:
            return JsonResponse({"error": "No input text provided"}, status=status.HTTP_400_BAD_REQUEST)
        if settings.USE_MOCK_OUTPUT:
            generated_text = f"This is mocked grammar checker for demonstration. \nInput text: {text}"
        else:
            response = check_grammar_with_openai(text)
            if isinstance(response, JsonResponse):
                return response
            else:
                generated_text = response
        # Save the generated text to a temporary .txt file
        text_file_name = "generated_text.txt"
        text_file_path = f"./tmp/{text_file_name}"

        with open(text_file_path, 'w', encoding="utf-8") as text_file:
            text_file.write(generated_text)
        # Read the .txt file to save to the History model
        with open(text_file_path, 'rb') as txt_file:
            txt_content = ContentFile(txt_file.read(), name=text_file_name)
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=txt_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(text_file_path)
        # Add the generated text to the response
        response_data = serializer.data
        response_data["text"] = generated_text
        # Return the serialized data with the generated text
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)

def write_post_with_openai(text):
    response_content = None
    try:
        # Step 1: Define prompts
        system_prompt = """You are a SMM.
                            You should write short post for the social media on given topic. Limit your response to 200 words."""
        user_prompt = f"This is a post topic: {text}"
        # Step 2: Prepare the API call to OpenAI with the uploaded file
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify your model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=256,
        )
        # Step 3: Get the response content
        if response.choices:
            response_content = response.choices[0].message.content

        return response_content if response_content else "No content generated."
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def post_writer(request, feature_key):
    if request.method == "POST":
        text = request.POST.get('text')
        if not text:
            return JsonResponse({"error": "No input text provided"}, status=status.HTTP_400_BAD_REQUEST)
        if settings.USE_MOCK_OUTPUT:
            generated_text = f"This is mocked post writer for demonstration. \nInput text: {text}"
        else:
            response = write_paragraph_with_openai(text)
            if isinstance(response, JsonResponse):
                return response
            else:
                generated_text = response
        # Save the generated text to a temporary .txt file
        text_file_name = "generated_text.txt"
        text_file_path = f"./tmp/{text_file_name}"

        with open(text_file_path, 'w', encoding="utf-8") as text_file:
            text_file.write(generated_text)
        # Read the .txt file to save to the History model
        with open(text_file_path, 'rb') as txt_file:
            txt_content = ContentFile(txt_file.read(), name=text_file_name)
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=txt_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(text_file_path)
        # Add the generated text to the response
        response_data = serializer.data
        response_data["text"] = generated_text
        # Return the serialized data with the generated text
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)

def document_code_with_openai(text):
    response_content = None
    try:
        # Step 1: Define prompts
        system_prompt = """You are a software developer.
                                You should document providen code snippet. Provide code explanation and variables used in this code"""
        user_prompt = f"This is a code to document: {text}. Limit your response to 200 words."
        # Step 2: Prepare the API call to OpenAI with the uploaded file
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify your model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=256,
        )
        # Step 3: Get the response content
        if response.choices:
            response_content = response.choices[0].message.content

        return response_content if response_content else "No content generated."
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def document_code(request, feature_key):
    if request.method == "POST":
        text = request.POST.get('text')
        if not text:
            return JsonResponse({"error": "No input text provided"}, status=status.HTTP_400_BAD_REQUEST)
        if settings.USE_MOCK_OUTPUT:
            generated_text = f"This is mocked code documentation for demonstration. \nInput text: {text}"
        else:
            response = document_code_with_openai(text)
            if isinstance(response, JsonResponse):
                return response
            else:
                generated_text = response
        # Save the generated text to a temporary .txt file
        text_file_name = "generated_text.txt"
        text_file_path = f"./tmp/{text_file_name}"

        with open(text_file_path, 'w', encoding="utf-8") as text_file:
            text_file.write(generated_text)
        # Read the .txt file to save to the History model
        with open(text_file_path, 'rb') as txt_file:
            txt_content = ContentFile(txt_file.read(), name=text_file_name)
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=txt_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(text_file_path)
        # Add the generated text to the response
        response_data = serializer.data
        response_data["text"] = generated_text
        # Return the serialized data with the generated text
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request"}, status=status.HTTP_400_BAD_REQUEST)

