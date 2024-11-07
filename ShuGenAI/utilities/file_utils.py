from io import BytesIO
import pikepdf
from PIL import Image
from django.core.files.base import ContentFile
from django.http import JsonResponse
from rest_framework import status
from features.models import History, Feature
from features.serializers import HistorySerializer
from django.contrib.staticfiles import finders
from pdf2docx import Converter
from docx import Document
import imageio
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
import PyPDF2
import os
import json
import csv
import pandas as pd
import xml.etree.ElementTree as ET
from moviepy.editor import VideoFileClip


def convert_pdf_to_docx(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_pdf = request.FILES["file"]
        # Create a temporary file for the uploaded PDF
        temp_pdf_path = f"/tmp/{uploaded_pdf.name}"
        # Save the uploaded PDF to a temporary location
        with open(temp_pdf_path, 'wb') as temp_file:
            for chunk in uploaded_pdf.chunks():
                temp_file.write(chunk)
        # Convert PDF to DOCX
        docx_path = temp_pdf_path.replace('.pdf', '.docx')
        cv = Converter(temp_pdf_path)
        cv.convert(docx_path, start=0, end=None)
        cv.close()
        # Read the DOCX file to save to the History model
        with open(docx_path, 'rb') as docx_file:
            docx_content = ContentFile(docx_file.read(), name=f"{uploaded_pdf.name.replace('.pdf', '.docx')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=docx_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_pdf_path)
        os.remove(docx_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no PDF provided"}, status=status.HTTP_400_BAD_REQUEST)

def convert_docx_to_pdf(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_docx = request.FILES["file"]
        # Save the uploaded DOCX temporarily
        temp_docx_path = f"/tmp/{uploaded_docx.name}"
        with open(temp_docx_path, 'wb') as temp_file:
            for chunk in uploaded_docx.chunks():
                temp_file.write(chunk)
        # Output PDF path
        temp_pdf_path = temp_docx_path.replace('.docx', '.pdf')
        try:
            # Load the DOCX file
            doc = Document(temp_docx_path)
            # Use Django's finders to locate the font in static files
            font_path = finders.find('fonts/times_new_roman.ttf')
            if not font_path:
                return JsonResponse({"error": "Font file not found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            # Register the custom font
            pdfmetrics.registerFont(TTFont("TimesNewRoman", font_path))
            # Set up PDF document and styles
            buffer = BytesIO()
            pdf_doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name='CustomStyle', fontName='TimesNewRoman', fontSize=12, leading=14))
            # Parse DOCX paragraphs with formatting
            content = []
            for paragraph in doc.paragraphs:
                # Convert DOCX runs into HTML-like tags for formatting
                para_text = ""
                for run in paragraph.runs:
                    run_text = run.text.replace('\n', '<br/>')
                    if run.bold:
                        run_text = f"<b>{run_text}</b>"
                    if run.italic:
                        run_text = f"<i>{run_text}</i>"
                    if run.underline:
                        run_text = f"<u>{run_text}</u>"
                    para_text += run_text
                # Add formatted text as Paragraph
                content.append(Paragraph(para_text, styles['CustomStyle']))
            # Build PDF
            pdf_doc.build(content)
            # Save the PDF content
            buffer.seek(0)
            pdf_content = ContentFile(buffer.read(), name=f"{uploaded_docx.name.replace('.docx', '.pdf')}")
            buffer.close()
            # Create History instance
            user = request.user if request.user.is_authenticated else None
            feature = Feature.objects.get(key=feature_key)
            history = History.objects.create(user=user, file=pdf_content, feature=feature)
            # Serialize History instance
            serializer = HistorySerializer(history, context={'request': request})
            # Clean up temporary files
            os.remove(temp_docx_path)
            return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            os.remove(temp_docx_path)  # Ensure temp DOCX is deleted even if PDF creation fails
            return JsonResponse({"error": f"Failed to convert DOCX to PDF: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return JsonResponse({"error": "Invalid request or no DOCX provided"}, status=status.HTTP_400_BAD_REQUEST)


def pdf_compression(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_pdf = request.FILES["file"]
        temp_pdf_path = f"/tmp/{uploaded_pdf.name}"
        # Save the uploaded PDF to a temporary location
        with open(temp_pdf_path, 'wb') as temp_file:
            for chunk in uploaded_pdf.chunks():
                temp_file.write(chunk)
        compressed_pdf_path = temp_pdf_path.replace('.pdf', '_compressed.pdf')
        try:
            # Open the PDF with pikepdf for compression
            with pikepdf.open(temp_pdf_path) as pdf:
                # Just save the PDF which may apply some internal optimizations
                pdf.save(compressed_pdf_path)  # No extra arguments
        except Exception as e:
            return JsonResponse({"error": f"An error occurred during compression with pikepdf: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Read the compressed PDF file to save to the History model
        with open(compressed_pdf_path, 'rb') as compressed_pdf_file:
            compressed_pdf_content = ContentFile(
                compressed_pdf_file.read(),
                name=f"{uploaded_pdf.name.replace('.pdf', '_compressed.pdf')}"
            )
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=compressed_pdf_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_pdf_path)
        os.remove(compressed_pdf_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no PDF provided"}, status=status.HTTP_400_BAD_REQUEST)
def convert_xml_to_json(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_xml = request.FILES["file"]
        # Create a temporary file for the uploaded XML
        temp_xml_path = f"/tmp/{uploaded_xml.name}"
        # Save the uploaded XML to a temporary location
        with open(temp_xml_path, 'wb') as temp_file:
            for chunk in uploaded_xml.chunks():
                temp_file.write(chunk)
        # Convert XML to JSON
        json_path = temp_xml_path.replace('.xml', '.json')
        with open(temp_xml_path, 'r') as xml_file:
            xml_content = xml_file.read()
            json_data = convert_xml_string_to_json(xml_content)
        # Save JSON data to a file
        with open(json_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=2)  # Use indent for pretty formatting
        # Read the JSON file to save to the History model
        with open(json_path, 'rb') as json_file:
            json_content = ContentFile(json_file.read(), name=f"{uploaded_xml.name.replace('.xml', '.json')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=json_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_xml_path)
        os.remove(json_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no XML provided"}, status=status.HTTP_400_BAD_REQUEST)


def convert_xml_string_to_json(xml_string):
    # Parse the XML string
    root = ET.fromstring(xml_string)
    def xml_to_dict(element):
        # Create a dictionary to hold the element data
        children = list(element)
        if len(children) == 0:  # No children, return text or None
            return element.text.strip() if element.text else None
        result = {}
        for child in children:
            # Get the child data
            child_data = xml_to_dict(child)
            # If the tag is already in the result, we append the data to a list
            if child.tag in result:
                # Ensure the value is a list
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]  # Convert to list if not already
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        return result
    # Start the conversion from the root element
    json_data = {root.tag: xml_to_dict(root)}
    return json_data

def convert_json_to_xml(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_json = request.FILES["file"]
        # Create a temporary file for the uploaded JSON
        temp_json_path = f"/tmp/{uploaded_json.name}"
        # Save the uploaded JSON to a temporary location
        with open(temp_json_path, 'wb') as temp_file:
            for chunk in uploaded_json.chunks():
                temp_file.write(chunk)
        # Convert JSON to XML
        xml_path = temp_json_path.replace('.json', '.xml')
        with open(temp_json_path, 'r') as json_file:
            json_content = json.load(json_file)
            xml_data = convert_json_to_xml_string(json_content)
        # Save XML data to a file
        with open(xml_path, 'w') as xml_file:
            xml_file.write(xml_data)
        # Read the XML file to save to the History model
        with open(xml_path, 'rb') as xml_file:
            xml_content = ContentFile(xml_file.read(), name=f"{uploaded_json.name.replace('.json', '.xml')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=xml_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_json_path)
        os.remove(xml_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no JSON provided"}, status=status.HTTP_400_BAD_REQUEST)


def convert_json_to_xml_string(json_data):
    def build_xml_element(data, root):
        if isinstance(data, dict):
            for key, value in data.items():
                sub_element = ET.SubElement(root, key)
                build_xml_element(value, sub_element)
        elif isinstance(data, list):
            for item in data:
                item_element = ET.SubElement(root, 'item')
                build_xml_element(item, item_element)
        else:
            root.text = str(data)
    root = ET.Element('root')  # Root element for the XML
    build_xml_element(json_data, root)
    xml_string = ET.tostring(root, encoding='unicode')
    return xml_string

def convert_xml_to_csv(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_xml = request.FILES["file"]
        # Create a temporary file for the uploaded XML
        temp_xml_path = f"/tmp/{uploaded_xml.name}"
        # Save the uploaded XML to a temporary location
        with open(temp_xml_path, 'wb') as temp_file:
            for chunk in uploaded_xml.chunks():
                temp_file.write(chunk)
        # Convert XML to CSV
        csv_path = temp_xml_path.replace('.xml', '.csv')
        data = parse_xml_to_dict(temp_xml_path)
        # Write the data to a CSV file
        with open(csv_path, 'w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            # Write header
            writer.writerow(data[0].keys())
            # Write data rows
            for row in data:
                writer.writerow(row.values())
        # Read the CSV file to save to the History model
        with open(csv_path, 'rb') as csv_file:
            csv_content = ContentFile(csv_file.read(), name=f"{uploaded_xml.name.replace('.xml', '.csv')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=csv_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_xml_path)
        os.remove(csv_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

    return JsonResponse({"error": "Invalid request or no XML provided"}, status=status.HTTP_400_BAD_REQUEST)

def parse_xml_to_dict(xml_path):
    # Parse the XML file and convert it to a list of dictionaries
    tree = ET.parse(xml_path)
    root = tree.getroot()
    data = []
    # Assuming each child of the root element is a record
    for elem in root:
        record = {}
        for child in elem:
            record[child.tag] = child.text
        data.append(record)
    return data


def flatten_json(y):
    """Flatten a nested JSON object."""
    out = {}
    def flatten(x, name=''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + '_')
        elif type(x) is list:
            for i, a in enumerate(x):
                flatten(a, name + str(i) + '_')
        else:
            out[name[:-1]] = x
    flatten(y)
    return out


def convert_json_to_csv(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_json = request.FILES["file"]
        # Create a temporary file for the uploaded JSON
        temp_json_path = f"/tmp/{uploaded_json.name}"
        # Save the uploaded JSON to a temporary location
        with open(temp_json_path, 'wb') as temp_file:
            for chunk in uploaded_json.chunks():
                temp_file.write(chunk)
        # Convert JSON to CSV
        csv_path = temp_json_path.replace('.json', '.csv')
        try:
            with open(temp_json_path, 'r') as json_file:
                json_data = json.load(json_file)
                # Check if the JSON data is a dictionary (handle single object)
                if isinstance(json_data, dict):
                    json_data = [flatten_json(json_data)]  # Wrap in a list for CSV writing
                elif isinstance(json_data, list) and all(isinstance(item, dict) for item in json_data):
                    json_data = [flatten_json(item) for item in json_data]  # Flatten each dict in the list
                else:
                    return JsonResponse({"error": "Invalid JSON format, expected a list of dictionaries."},
                                        status=status.HTTP_400_BAD_REQUEST)
                # Write the data to a CSV file
                with open(csv_path, 'w', newline='') as csv_file:
                    if json_data:
                        writer = csv.DictWriter(csv_file, fieldnames=json_data[0].keys())
                        writer.writeheader()
                        writer.writerows(json_data)
                    else:
                        return JsonResponse({"error": "No data to write to CSV."}, status=status.HTTP_400_BAD_REQUEST)
        except json.JSONDecodeError as e:
            return JsonResponse({"error": f"Invalid JSON file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Read the CSV file to save to the History model
        with open(csv_path, 'rb') as csv_file:
            csv_content = ContentFile(csv_file.read(), name=f"{uploaded_json.name.replace('.json', '.csv')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=csv_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_json_path)
        os.remove(csv_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no JSON provided"}, status=status.HTTP_400_BAD_REQUEST)


def convert_xls_to_csv(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_xls = request.FILES["file"]
        # Create a temporary file for the uploaded XLS
        temp_xls_path = f"/tmp/{uploaded_xls.name}"
        # Save the uploaded XLS to a temporary location
        with open(temp_xls_path, 'wb') as temp_file:
            for chunk in uploaded_xls.chunks():
                temp_file.write(chunk)
        # Convert XLS to CSV
        csv_path = temp_xls_path.replace('.xls', '.csv').replace('.xlsx', '.csv')
        try:
            # Use pandas to read the XLS file and convert it to CSV
            df = pd.read_excel(temp_xls_path)
            df.to_csv(csv_path, index=False)
        except Exception as e:
            return JsonResponse({"error": f"Error converting file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        # Read the CSV file to save to the History model
        with open(csv_path, 'rb') as csv_file:
            csv_content = ContentFile(csv_file.read(), name=f"{uploaded_xls.name.replace('.xls', '.csv').replace('.xlsx', '.csv')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=csv_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_xls_path)
        os.remove(csv_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no XLS file provided"}, status=status.HTTP_400_BAD_REQUEST)

def convert_xls_to_json(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_xls = request.FILES["file"]
        # Create a temporary file for the uploaded XLS
        temp_xls_path = f"/tmp/{uploaded_xls.name}"
        # Save the uploaded XLS to a temporary location
        with open(temp_xls_path, 'wb') as temp_file:
            for chunk in uploaded_xls.chunks():
                temp_file.write(chunk)
        # Convert XLS to JSON
        json_path = temp_xls_path.replace('.xls', '.json').replace('.xlsx', '.json')
        try:
            # Use pandas to read the XLS file and convert it to JSON
            df = pd.read_excel(temp_xls_path)
            json_data = df.to_json(orient='records')
            with open(json_path, 'w') as json_file:
                json_file.write(json_data)
        except Exception as e:
            return JsonResponse({"error": f"Error converting file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        # Read the JSON file to save to the History model
        with open(json_path, 'rb') as json_file:
            json_content = ContentFile(json_file.read(), name=f"{uploaded_xls.name.replace('.xls', '.json').replace('.xlsx', '.json')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=json_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_xls_path)
        os.remove(json_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no XLS file provided"}, status=status.HTTP_400_BAD_REQUEST)

def convert_xls_to_xml(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_xls = request.FILES["file"]
        # Create a temporary file for the uploaded XLS
        temp_xls_path = f"/tmp/{uploaded_xls.name}"
        # Save the uploaded XLS to a temporary location
        with open(temp_xls_path, 'wb') as temp_file:
            for chunk in uploaded_xls.chunks():
                temp_file.write(chunk)
        # Convert XLS to XML
        xml_path = temp_xls_path.replace('.xls', '.xml').replace('.xlsx', '.xml')
        try:
            # Use pandas to read the XLS file
            df = pd.read_excel(temp_xls_path)
            # Rename columns to make them XML-compatible (replace spaces, prefix numbers)
            df.columns = [
                f"Column_{col}" if isinstance(col, int) or str(col)[0].isdigit() else str(col).replace(" ", "_")
                for col in df.columns
            ]
            # Convert the DataFrame to XML
            xml_data = df.to_xml(index=False, root_name='Records', row_name='Record')
            # Save XML data to a file
            with open(xml_path, 'w') as xml_file:
                xml_file.write(xml_data)
        except Exception as e:
            return JsonResponse({"error": f"Error converting file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        # Read the XML file to save to the History model
        with open(xml_path, 'rb') as xml_file:
            xml_content = ContentFile(xml_file.read(), name=f"{uploaded_xls.name.replace('.xls', '.xml').replace('.xlsx', '.xml')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=xml_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_xls_path)
        os.remove(xml_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no XLS file provided"}, status=status.HTTP_400_BAD_REQUEST)


def convert_mp4_to_gif(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_video = request.FILES["file"]
        temp_video_path = f"/tmp/{uploaded_video.name}"
        # Save the uploaded video to a temporary location
        with open(temp_video_path, 'wb') as temp_file:
            for chunk in uploaded_video.chunks():
                temp_file.write(chunk)
        gif_path = temp_video_path.replace('.mp4', '.gif')
        try:
            # Load the video
            clip = VideoFileClip(temp_video_path)
            # Resize the clip and adjust duration and frame rate
            resized_clip = clip.resize(width=240)  # Resize width
            resized_clip = resized_clip.set_duration(min(clip.duration, 5))  # Limit duration to 5 seconds
            resized_clip.fps = 10  # Lower frame rate for smoother GIF
            # Convert to GIF with imageio for better control
            frames = []
            for frame in resized_clip.iter_frames(fps=resized_clip.fps, dtype='uint8'):
                # Convert frame to a format suitable for GIF
                image = Image.fromarray(frame)
                frames.append(image)
            # Save frames to GIF
            frames[0].save(gif_path, save_all=True, append_images=frames[1:], loop=0, duration=100)  # 100ms per frame
        except Exception as e:
            return JsonResponse({"error": f"An error occurred during conversion: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Read the GIF file to save to the History model
        with open(gif_path, 'rb') as gif_file:
            gif_content = ContentFile(gif_file.read(), name=f"{uploaded_video.name.replace('.mp4', '.gif')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=gif_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_video_path)
        os.remove(gif_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no video provided"}, status=status.HTTP_400_BAD_REQUEST)

def convert_mkv_to_mp4(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_video = request.FILES["file"]
        # Create a temporary file for the uploaded MKV
        temp_mkv_path = f"/tmp/{uploaded_video.name}"
        # Save the uploaded MKV to a temporary location
        with open(temp_mkv_path, 'wb') as temp_file:
            for chunk in uploaded_video.chunks():
                temp_file.write(chunk)
        # Convert the MKV to MP4
        mp4_path = temp_mkv_path.replace('.mkv', '.mp4')  # Change extension as needed
        try:
            # Load the MKV video and write to MP4
            clip = VideoFileClip(temp_mkv_path)
            clip.write_videofile(mp4_path, codec='libx264', audio_codec='aac')
        except Exception as e:
            return JsonResponse({"error": f"An error occurred during conversion: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Read the MP4 file to save to the History model
        with open(mp4_path, 'rb') as mp4_file:
            mp4_content = ContentFile(mp4_file.read(), name=f"{uploaded_video.name.replace('.mkv', '.mp4')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=mp4_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_mkv_path)
        os.remove(mp4_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no MKV provided"}, status=status.HTTP_400_BAD_REQUEST)

def convert_mp4_to_mp3(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_video = request.FILES["file"]
        # Create a temporary file for the uploaded MP4
        temp_mp4_path = f"/tmp/{uploaded_video.name}"
        # Save the uploaded MP4 to a temporary location
        with open(temp_mp4_path, 'wb') as temp_file:
            for chunk in uploaded_video.chunks():
                temp_file.write(chunk)
        # Extract audio from the MP4 and save as MP3
        mp3_path = temp_mp4_path.replace('.mp4', '.mp3')  # Change extension as needed
        try:
            # Load the MP4 video
            video = VideoFileClip(temp_mp4_path)
            # Extract audio and write to MP3
            audio = video.audio
            audio.write_audiofile(mp3_path, codec='mp3')
        except Exception as e:
            return JsonResponse({"error": f"An error occurred during audio extraction: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # Read the MP3 file to save to the History model
        with open(mp3_path, 'rb') as mp3_file:
            mp3_content = ContentFile(mp3_file.read(), name=f"{uploaded_video.name.replace('.mp4', '.mp3')}")
        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)
        # Create and save the History instance
        history = History.objects.create(user=user, file=mp3_content, feature=feature)
        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})
        # Clean up temporary files
        os.remove(temp_mp4_path)
        os.remove(mp3_path)
        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)
    return JsonResponse({"error": "Invalid request or no MP4 provided"}, status=status.HTTP_400_BAD_REQUEST)


def compress_mp4(request, feature_key):
    if request.method == "POST" and request.FILES.get("file"):
        uploaded_video = request.FILES["file"]
        temp_video_path = f"/tmp/{uploaded_video.name}"

        # Save the uploaded video to a temporary location
        with open(temp_video_path, 'wb') as temp_file:
            for chunk in uploaded_video.chunks():
                temp_file.write(chunk)

        # Set the path for the compressed video
        compressed_video_path = temp_video_path.replace('.mp4', '_compressed.mp4')
        try:
            # Load the video file
            video = VideoFileClip(temp_video_path)

            # Compress the video with adjusted parameters
            video.write_videofile(
                compressed_video_path,
                codec='libx264',
                bitrate='800k',  # Reduced bitrate
                audio_codec='aac',  # Ensure audio codec is set for compatibility
                preset='slow',  # Compression preset (you can also try 'slow' or 'fast')
                fps=25  # Optional: Lower the frame rate
            )
        except Exception as e:
            return JsonResponse({"error": f"An error occurred during video compression: {str(e)}"},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Read the compressed video file to save to the History model
        with open(compressed_video_path, 'rb') as compressed_file:
            compressed_content = ContentFile(compressed_file.read(),
                                             name=f"{uploaded_video.name.replace('.mp4', '_compressed.mp4')}")

        # Get the user and feature
        user = request.user if request.user.is_authenticated else None
        feature = Feature.objects.get(key=feature_key)

        # Create and save the History instance
        history = History.objects.create(user=user, file=compressed_content, feature=feature)

        # Serialize the History instance
        serializer = HistorySerializer(history, context={'request': request})

        # Clean up temporary files
        os.remove(temp_video_path)
        os.remove(compressed_video_path)

        # Return the serialized data
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

    return JsonResponse({"error": "Invalid request or no video provided"}, status=status.HTTP_400_BAD_REQUEST)
