# barbearia_app/services.py (VERSÃO FINAL - LÓGICA INTELIGENTE DE DIAS)

import re
from datetime import datetime, timedelta, time, date
from django.db.models import Q
from .models import Agendamento, Barbeiro, Servico, Feriado, Cliente, BarbeiroIndisponibilidade, ConfiguracaoGeral
from django.utils import timezone
from django.db import transaction
from twilio.rest import Client
from django.conf import settings
import json
import unicodedata

DIAS_MAX_ANTECEDENCIA = 90
WHATSAPP_CONFIRMATION_TEMPLATE_SID = settings.WHATSAPP_CONFIRMATION_TEMPLATE_SID

# --- Função Auxiliar: Pega a Configuração ---
def get_config():
    try:
        return ConfiguracaoGeral.objects.get(pk=1)
    except ConfiguracaoGeral.DoesNotExist:
        # Cria padrão se não existir
        return ConfiguracaoGeral.objects.create(pk=1)

# --- Funções Auxiliares de Data ---
def _resolve_date(texto_data: str) -> date | None:
    if not isinstance(texto_data, str): return None
    texto_data = texto_data.lower().strip()
    hoje = timezone.localtime(timezone.now()).date()

    if "hoje" in texto_data: return hoje
    if "amanhã" in texto_data or "amanha" in texto_data: return hoje + timedelta(days=1)

    dias = {"segunda": 0, "terça": 1, "terca": 1, "quarta": 2, "quinta": 3, "sexta": 4, "sábado": 5, "sabado": 5, "domingo": 6}
    for dia_nome, dia_num in dias.items():
        if dia_nome in texto_data:
            if "próxima" in texto_data or "proxima" in texto_data:
                dias_a_frente = (dia_num - hoje.weekday() + 7) % 7
                if dias_a_frente == 0: dias_a_frente = 7
                return hoje + timedelta(days=dias_a_frente)
            else:
                dias_a_frente = (dia_num - hoje.weekday()) % 7
                if dias_a_frente < 0: dias_a_frente += 7
                return hoje + timedelta(days=dias_a_frente)

    formats_to_try = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
    for fmt in formats_to_try:
        try: return datetime.strptime(texto_data, fmt).date()
        except (ValueError, TypeError): continue
    return None

def _get_datetime_from_time(dt_date, dt_time):
    return timezone.make_aware(datetime.combine(dt_date, dt_time))

def is_feriado(data):
    return Feriado.objects.filter(data_feriado=data).exists()

def get_barbeiro_indisponibilidade_periodo(barbeiro_id, data):
    return BarbeiroIndisponibilidade.objects.filter(barbeiro_id=barbeiro_id, data_inicio__lte=data, data_fim__gte=data).first()

def enviar_whatsapp_mensagem(telefone_cliente, template_sid, template_vars):
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    if not telefone_cliente.startswith('+'): telefone_cliente = f'+55{telefone_cliente}'
    try:
        content_variables_payload = {"1": template_vars["1"], "2": template_vars["2"], "3": template_vars["3"], "4": template_vars["4"], "5": template_vars["5"]}
        client.messages.create(
            from_=f'whatsapp:{settings.TWILIO_PHONE_NUMBER}',
            to=f'whatsapp:{telefone_cliente}',
            content_sid=template_sid,
            content_variables=json.dumps(content_variables_payload)
        )
        return {"success": True}
    except Exception as e:
        print(f"Erro WhatsApp: {e}")
        return {"success": False, "message": str(e)}


# =========================================================
# 🚀 FUNÇÃO PRINCIPAL: CALCULA HORÁRIOS BASEADO NA CONFIG
# =========================================================
def get_horarios_disponiveis(data_str, servico_id, barbeiro_id=None):
    # 1. Carrega Configuração
    config = get_config()
    
    # 2. Valida Data
    try:
        if isinstance(data_str, str):
            data_obj = _resolve_date(data_str)
            if data_obj is None: data_obj = datetime.strptime(data_str, '%Y-%m-%d').date()
        else:
            data_obj = data_str
    except:
        return {"success": False, "message": "Data inválida."}

    hoje_local = timezone.localtime(timezone.now()).date()
    if data_obj < hoje_local: return {"success": False, "message": "Data no passado."}
    if data_obj > (hoje_local + timedelta(days=DIAS_MAX_ANTECEDENCIA)):
        return {"success": False, "message": f"Agendamento permitido apenas com {DIAS_MAX_ANTECEDENCIA} dias de antecedência."}

    # 3. LÓGICA DE SELEÇÃO DE HORÁRIOS DO DIA (O Cérebro)
    # Define os horários padrão (Seg-Sex)
    abertura = config.hora_abertura
    fechamento = config.hora_fechamento
    tem_almoco = True # Seg-Sex tem almoço por padrão

    # Sobrescreve se for Feriado, Domingo ou Sábado
    if is_feriado(data_obj):
        if not config.trabalha_feriados:
            return {"success": False, "message": "A barbearia estará fechada neste feriado."}
        abertura = config.hora_abertura_feriado
        fechamento = config.hora_fechamento_feriado
        tem_almoco = False # Feriado geralmente é direto (ou configure se quiser)

    elif data_obj.weekday() == 6: # Domingo
        if not config.abre_domingo:
            return {"success": False, "message": "A barbearia não abre aos domingos."}
        abertura = config.hora_abertura_domingo
        fechamento = config.hora_fechamento_domingo
        tem_almoco = False # Domingo geralmente é tiro curto

    elif data_obj.weekday() == 5: # Sábado
        if not config.abre_sabado:
            return {"success": False, "message": "A barbearia não abre aos sábados."}
        abertura = config.hora_abertura_sabado
        fechamento = config.hora_fechamento_sabado
        tem_almoco = False # Sábado geralmente vai direto até as 14h/15h

    # 4. Busca Serviço e Barbeiros
    try: servico = Servico.objects.get(id=servico_id)
    except Servico.DoesNotExist: return {"success": False, "message": "Serviço não encontrado."}

    barbeiros_a_verificar = Barbeiro.objects.filter(id=barbeiro_id) if barbeiro_id else Barbeiro.objects.all()
    if not barbeiros_a_verificar.exists(): return {"success": False, "message": "Barbeiro não encontrado."}

    disponibilidades = []
    
    # Usa os horários decididos acima
    start_of_day_dt = _get_datetime_from_time(data_obj, abertura)
    fim_do_dia_dt = _get_datetime_from_time(data_obj, fechamento)

    for barbeiro in barbeiros_a_verificar:
        if get_barbeiro_indisponibilidade_periodo(barbeiro.id, data_obj): continue

        agendamentos = Agendamento.objects.filter(barbeiro=barbeiro, data_agendada=data_obj, hora_fim__isnull=False).exclude(status='cancelado')

        # Define slot inicial baseado na grade da config
        slot_atual = start_of_day_dt
        
        # Se for hoje, ajusta para o próximo intervalo válido
        if data_obj == hoje_local:
            agora = timezone.localtime(timezone.now())
            if agora > slot_atual:
                # Arredonda para cima no intervalo (ex: 30 min)
                minutos_extra = config.intervalo_agendamento - (agora.minute % config.intervalo_agendamento)
                slot_atual = agora + timedelta(minutes=minutos_extra)
                slot_atual = slot_atual.replace(second=0, microsecond=0) # Limpa segundos

        # Loop de geração de slots
        while slot_atual + timedelta(minutes=servico.duracao_minutos) <= fim_do_dia_dt:
            slot_fim = slot_atual + timedelta(minutes=servico.duracao_minutos)

            # Checagem de Almoço (Só se tem_almoco for True naquele dia)
            pula_slot = False
            if tem_almoco:
                almoco_ini = _get_datetime_from_time(data_obj, config.hora_inicio_almoco)
                almoco_fim = _get_datetime_from_time(data_obj, config.hora_fim_almoco)
                # Se o serviço cai dentro ou atravessa o almoço
                if (slot_atual < almoco_fim and slot_fim > almoco_ini):
                    pula_slot = True
            
            if pula_slot:
                # Pula para o fim do almoço e tenta de novo
                slot_atual = _get_datetime_from_time(data_obj, config.hora_fim_almoco)
                continue

            # Checagem de Conflitos com Agendamentos
            conflito = False
            for agend in agendamentos:
                ini = _get_datetime_from_time(agend.data_agendada, agend.hora_inicio)
                fim = _get_datetime_from_time(agend.data_agendada, agend.hora_fim)
                # Interseção de horários
                if (slot_atual < fim and slot_fim > ini):
                    conflito = True
                    break
            
            if not conflito:
                disponibilidades.append({
                    'barbeiro_id': barbeiro.id,
                    'barbeiro_nome': barbeiro.nome_completo,
                    'hora_inicio': slot_atual.strftime('%H:%M')
                })

            # Avança a grade
            slot_atual += timedelta(minutes=config.intervalo_agendamento)

    if not disponibilidades: return {"success": False, "message": "Agenda cheia para esta data."}
    
    # Remove duplicatas (mesmo horário para barbeiros diferentes) e ordena
    uniques = {}
    for d in disponibilidades: uniques[(d['hora_inicio'], d['barbeiro_id'])] = d
    final_list = sorted(uniques.values(), key=lambda x: x['hora_inicio'])
    
    return {"success": True, "horarios": final_list}


def find_cliente_by_telefone(telefone: str):
    telefone_limpo = re.sub(r'\D', '', telefone)
    try:
        cliente = Cliente.objects.get(telefone=telefone_limpo)
        return {"success": True, "nome_completo": cliente.nome_completo, "id": cliente.id}
    except Cliente.DoesNotExist:
        return {"success": False, "message": "Cliente não encontrado."}

def criar_agendamento(nome_cliente, telefone_cliente, servico_id, data_agendada_str, hora_inicio_str, barbeiro_id):
    data_agendada = _resolve_date(data_agendada_str)
    if data_agendada is None: return {"success": False, "message": "Formato de data inválido."}
    try:
        hora_inicio = datetime.strptime(hora_inicio_str, '%H:%M').time()
        servico = Servico.objects.get(id=servico_id)
        barbeiro_obj = Barbeiro.objects.get(id=barbeiro_id)
    except Exception: return {"success": False, "message": "Dados inválidos."}

    telefone_limpo = re.sub(r'\D', '', telefone_cliente)
    
    with transaction.atomic():
        cliente, _ = Cliente.objects.get_or_create(telefone=telefone_limpo)
        if cliente.nome_completo != nome_cliente:
            cliente.nome_completo = nome_cliente
            cliente.save()
        
        # Verifica conflito final (Double Booking check)
        agendamento_inicio = _get_datetime_from_time(data_agendada, hora_inicio)
        agendamento_fim = agendamento_inicio + timedelta(minutes=servico.duracao_minutos)
        
        conflitos = Agendamento.objects.filter(
            barbeiro=barbeiro_obj, data_agendada=data_agendada, hora_fim__isnull=False,
            status__in=['confirmado', 'pendente']
        )
        
        for agend in conflitos:
            ini = _get_datetime_from_time(agend.data_agendada, agend.hora_inicio)
            fim = _get_datetime_from_time(agend.data_agendada, agend.hora_fim)
            if (agendamento_inicio < fim and agendamento_fim > ini):
                return {"success": False, "message": "Este horário acabou de ser ocupado."}

        try:
            agendamento = Agendamento.objects.create(
                cliente=cliente, barbeiro=barbeiro_obj, servico=servico,
                data_agendada=data_agendada, hora_inicio=hora_inicio, status='pendente'
            )
            
            # Envia WhatsApp
            template_vars = {
                '1': cliente.nome_completo, '2': servico.nome_servico,
                '3': barbeiro_obj.nome_completo, '4': data_agendada.strftime('%d/%m/%Y'), '5': hora_inicio_str
            }
            enviar_whatsapp_mensagem(cliente.telefone, settings.WHATSAPP_CONFIRMATION_TEMPLATE_SID, template_vars)
            
            return {"success": True, "message": "Agendamento realizado!", "agendamento_id": agendamento.id}
        except Exception as e:
            return {"success": False, "message": f"Erro ao salvar: {e}"}

def get_servicos(): return list(Servico.objects.all().values('id', 'nome_servico', 'preco', 'duracao_minutos'))
def get_barbeiros(): return list(Barbeiro.objects.all().values('id', 'nome_completo', 'especialidade'))