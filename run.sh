#!/bin/bash

python3 ShuGenAI/manage.py makemigrations
python3 ShuGenAI/manage.py migrate
python3 ShuGenAI/manage.py runserver 0.0.0.0:8000