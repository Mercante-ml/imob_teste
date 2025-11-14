# barbearia_app/urls.py
from django.urls import path
from . import views 

urlpatterns = [
    path('', views.index, name='index'), 
    path('chat/', views.chat_interaction, name='chat_interaction'), 
    path('painel/', views.painel_atendimento, name='painel_atendimento'), 
    #path('twilio-sms-webhook/', views.twilio_sms_webhook, name='twilio_sms_webhook'),
    path('twilio-whatsapp-webhook/', views.twilio_whatsapp_webhook, name='twilio_whatsapp_webhook'),
    path('dashboard/geral/', views.dashboard_visao_geral, name='dashboard_geral'),
]