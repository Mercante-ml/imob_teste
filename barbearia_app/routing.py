# barbearia_app/routing.py
from django.urls import path
from .consumers import DashConsumer

websocket_urlpatterns = [
    path('ws/dpd/<slug:dpd_name>/', DashConsumer.as_asgi()),
]
