import os
import django
from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from django.core.asgi import get_asgi_application

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

# Create main FastAPI application
application = FastAPI(title="Healthcare Chatbot")

# Mount Django WSGI application
django_app = get_asgi_application()
application.mount("/django", WSGIMiddleware(django_app))

# You'll add FastAPI routes here later