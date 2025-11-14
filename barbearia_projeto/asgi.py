# barbearia_projeto/asgi.py (VERSÃO CORRIGIDA FINALMENTE)

import os
from django.core.asgi import get_asgi_application

# 1. Carrega o settings do Django PRIMEIRO de tudo
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_projeto.settings')

# 2. Inicializa a aplicação Django (isso carrega todos os settings)
django_asgi_app = get_asgi_application()

# 3. AGORA que o Django está pronto, podemos importar o Dash/Channels
from channels.routing import ProtocolTypeRouter
from channels.security.websocket import AllowedHostsOriginValidator
import django_plotly_dash.routing

# 4. Define o roteador
application = ProtocolTypeRouter({
    # Conexões HTTP (normais) vão para o Django
    "http": django_asgi_app,

    # Conexões WebSocket (do Dash)
    "websocket": AllowedHostsOriginValidator(
        # A CORREÇÃO ESTÁ AQUI: (Removemos o URLRouter)
        django_plotly_dash.routing.application
    ),
})