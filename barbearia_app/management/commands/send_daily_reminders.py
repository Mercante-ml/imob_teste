# barbearia_app/management/commands/send_daily_reminders.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime, time
from barbearia_app.models import Agendamento
from barbearia_app.services import enviar_whatsapp_mensagem
from django.conf import settings # Importar settings para o SID do template

class Command(BaseCommand):
    help = 'Envia lembretes diários de agendamentos via WhatsApp para agendamentos pendentes no dia.'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando envio de lembretes diários...")

        hoje = timezone.localtime(timezone.now()).date()
        agora = timezone.localtime(timezone.now()).time()

        # Definir um limite de tempo para enviar lembretes.
        # Por exemplo, não enviar lembretes para agendamentos que já passaram ou estão muito próximos.
        # Vamos considerar agendamentos que começam pelo menos 15 minutos no futuro a partir de agora.
        # Ajuste este valor conforme sua necessidade.
        min_time_for_reminder = (datetime.combine(hoje, agora) + timedelta(minutes=15)).time()

        # Buscar agendamentos para hoje que ainda não foram concluídos/cancelados
        # E, CRUCIALMENTE, que AINDA NÃO TIVERAM O LEMBRETE ENVIADO
        # E que o horário de início ainda não passou (ou está no futuro próximo)
        agendamentos_do_dia = Agendamento.objects.filter(
            data_agendada=hoje,
            status__in=['pendente'], # Enviar lembretes para pendentes e confirmados
            lembrete_diario_enviado=False, # Apenas para agendamentos que não receberam lembrete
            hora_inicio__gte=min_time_for_reminder # Apenas para horários futuros ou próximos
        ).select_related('cliente', 'barbeiro', 'servico') # Otimiza o acesso aos dados relacionados

        if not agendamentos_do_dia.exists():
            self.stdout.write("Nenhum agendamento elegível para lembrete hoje.")
            return

        WHATSAPP_REMINDER_TEMPLATE_SID_FROM_SETTINGS = settings.WHATSAPP_DAILY_REMINDER_TEMPLATE_SID

        for agendamento in agendamentos_do_dia:
            nome_cliente = agendamento.cliente.nome_completo
            telefone_cliente = agendamento.cliente.telefone
            data_agendada_formatada = agendamento.data_agendada.strftime('%d/%m/%Y')
            hora_inicio = agendamento.hora_inicio.strftime('%H:%M')
            barbeiro_nome = agendamento.barbeiro.nome_completo
            servico_nome = agendamento.servico.nome_servico

            # Variáveis para o template do WhatsApp
            template_vars = {
                '1': nome_cliente,
                '2': data_agendada_formatada,
                '3': hora_inicio,
                '4': barbeiro_nome,
                '5': servico_nome,
                '6': settings.WHATSAPP_CHAT_LINK # Link para o chat, se houver
            }

            self.stdout.write(f"Tentando enviar lembrete para {nome_cliente} ({telefone_cliente}) para {data_agendada_formatada} às {hora_inicio}...")

            whatsapp_result = enviar_whatsapp_mensagem(
                telefone_cliente=telefone_cliente,
                template_sid=WHATSAPP_REMINDER_TEMPLATE_SID_FROM_SETTINGS,
                template_vars=template_vars
            )

            if whatsapp_result["success"]:
                self.stdout.write(self.style.SUCCESS(f"Lembrete enviado com sucesso para {nome_cliente}."))
                # MARCAR O AGENDAMENTO COMO LEMBRETE ENVIADO
                agendamento.lembrete_diario_enviado = True
                agendamento.save(update_fields=['lembrete_diario_enviado'])
            else:
                self.stdout.write(self.style.ERROR(f"Falha ao enviar lembrete para {nome_cliente}: {whatsapp_result['message']}"))

        self.stdout.write("Envio de lembretes diários concluído.")