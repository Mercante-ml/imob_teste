"""
Django settings for barbearia_projeto project.
(VERSÃO FINAL PARA POSTGRES + DOCKER)
"""

from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# Carrega as variáveis de ambiente do arquivo .env
# (O Docker-compose já faz isso, mas é bom ter para rodar localmente sem Docker)
load_dotenv(os.path.join(Path(__file__).resolve().parent.parent, '.env'))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# LIDO DO .ENV
SECRET_KEY = os.getenv('SECRET_KEY') 

# LIDO DO .ENV (Default 'False' é mais seguro para produção)
DEBUG = os.getenv('DEBUG', 'False') == 'True'

# LIDO DO .ENV (Lê as strings separadas por vírgula)
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',    
    'whitenoise.runserver_nostatic',
    'barbearia_app.apps.BarbeariaAppConfig',
    'django_plotly_dash.apps.DjangoPlotlyDashConfig',
    'channels',
    'channels_redis',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'barbearia_projeto.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'barbearia_projeto.wsgi.application'


# ===================================================================
# ### CONFIGURAÇÃO DO BANCO DE DADOS (A MUDANÇA PRINCIPAL) ###
# ===================================================================

DATABASES = {
    'default': dj_database_url.config(
        # Lê a 'DATABASE_URL' do .env
        conn_max_age=600 # Tempo máximo de vida da conexão do BD
    )
}
#
# REMOVEMOS O 'default=sqlite...'
# Se 'DATABASE_URL' não estiver no .env, o Django agora vai falhar
# (o que é o comportamento correto e seguro).
#
# ===================================================================


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    # ... (validadores padrão) ...
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [ 
    os.path.join(BASE_DIR, 'static'),
]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles') 

# Mídia (Uploads de Logo)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Configuração do WhiteNoise (DEPOIS de STATIC_ROOT)
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# NOVO: Configuração de segurança para o Render/produção
# LIDO DO .ENV
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://127.0.0.1,http://localhost').split(',')
# (Para o Render, você vai adicionar 'https://barbearia-chatbot.onrender.com' no .env)


LOGIN_REDIRECT_URL = '/painel/'  
LOGOUT_REDIRECT_URL = '/'        


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configuração do Twilio (lido do .env)
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_PHONE_NUMBER = os.environ.get('TWILIO_PHONE_NUMBER')

WHATSAPP_CONFIRMATION_TEMPLATE_SID = os.environ.get('WHATSAPP_CONFIRMATION_TEMPLATE_SID')
WHATSAPP_DAILY_REMINDER_TEMPLATE_SID = os.environ.get('WHATSAPP_DAILY_REMINDER_TEMPLATE_SID')
WHATSAPP_CHAT_LINK = os.environ.get('WHATSAPP_CHAT_LINK')


# Diz ao Django para usar o Channels (para WebSockets)
ASGI_APPLICATION = 'barbearia_projeto.asgi.application'

# Configura o Redis (o "motor" do Channels)
# Ele vai procurar um serviço chamado 'redis' no Docker
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('redis', 6379)],
        },
    },
}

# Configuração de segurança do Dash
X_FRAME_OPTIONS = 'SAMEORIGIN'

# ===============================================
# --- CONFIGURAÇÃO DO PLOTLY DASH ---
# ===============================================
PLOTLY_DASH = {
    # Diz ao Dash para checar o login do Django ANTES de carregar
    "autentication_required": True,

    # Garante que os gráficos sejam embutidos corretamente
    "serve_locally": True,
}