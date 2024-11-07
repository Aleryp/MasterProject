#!/bin/bash

python ShuGenAI/manage.py makemigrations
python ShuGenAI/manage.py migrate
python ShuGenAI/manage.py runserver 0.0.0.0:8000