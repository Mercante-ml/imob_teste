# barbearia_projeto/urls.py (VERSÃO FINAL E CORRIGIDA)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Removido: from barbearia_app import views (não importamos views diretamente aqui)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')), 
    path('django_plotly_dash/', include('django_plotly_dash.urls')),
    path('', include('barbearia_app.urls')), 
]

# NOVO: Adiciona a rota de Mídia apenas em modo DEBUG
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)