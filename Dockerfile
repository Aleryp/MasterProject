FROM python:3.10-slim
LABEL authors="aleryp"
# Use an official Python image

# Set environment variables for Django
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies for Django and ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install -r requirements.txt

# Copy Django project
COPY . /app/

# Expose the port Django will run on
EXPOSE 8000

# Run Django's development server
CMD ["gunicorn", "ShuGenAI.wsgi:application", "--bind", "0.0.0.0:8000"]