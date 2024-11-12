# Use an NVIDIA CUDA base image for Python with GPU support
FROM nvidia/cuda:11.2.2-cudnn8-runtime-ubuntu20.04

LABEL authors="aleryp"

# Set environment variables for Django
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies and Python 3.10
RUN apt-get update && \
    apt-get install -y \
    software-properties-common \
    wget \
    curl \
    ffmpeg && \
    # Add Python 3.10 repository
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-dev python3.10-venv && \
    # Install pip for Python 3.10
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py && \
    python3.10 get-pip.py && \
    # Ensure python3.10 is used as default
    ln -sf /usr/bin/python3.10 /usr/bin/python3 && \
    ln -sf /usr/bin/pip3 /usr/bin/pip && \
    rm -rf /var/lib/apt/lists/* && \
    rm get-pip.py

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
