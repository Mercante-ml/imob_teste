# barbearia_app/apps.py
from django.apps import AppConfig

class BarbeariaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'barbearia_app'

    def ready(self):
        # 1. Carrega os filtros customizados
        import barbearia_app.templatetags.custom_filters
        
        # 2. NOVO: Carrega e registra os dashboards do Plotly
        import barbearia_app.dashboards