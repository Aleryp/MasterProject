# Use an NVIDIA CUDA base image for Python with GPU support
FROM nvidia/cuda:11.2.2-cudnn8-runtime-ubuntu20.04

LABEL authors="aleryp"

# Set environment variables for Django
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies for Django and ffmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg python3-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy Django project
COPY . /app/
RUN chmod +x /app/run.sh

# Expose the port Django will run on
EXPOSE 8000

# Run Django's development server
CMD ["gunicorn", "ShuGenAI.wsgi:application", "--bind", "0.0.0.0:8000"]
