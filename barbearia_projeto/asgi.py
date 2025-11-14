# barbearia_projeto/asgi.py
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import barbearia_app.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_projeto.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            barbearia_app.routing.websocket_urlpatterns
        )
    ),
})
