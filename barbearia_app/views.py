# barbearia_app/views.py (VERSÃO COM LÓGICA "INTELIGENTE" DE BARBEIROS)

# barbearia_app/views.py (VERSÃO COM MESES TRADUZIDOS)

import json
import traceback
import re
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Agendamento, Barbeiro, Servico, Cliente, ConfiguracaoGeral
from django.utils import timezone
from datetime import datetime, date, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from . import services
from twilio.twiml.messaging_response import MessagingResponse

session_histories = {}

def get_session_history(session_id: str) -> list:
    if session_id not in session_histories:
        session_histories[session_id] = []
    return session_histories[session_id]

def is_gerente(user):
    return user.is_authenticated and user.groups.filter(name='Gerentes').exists()

def index(request):
    session_id = request.session.session_key
    if not session_id:
        request.session.create() 
        session_id = request.session.session_key 

    request.session['agendamento_state'] = {'step': 'welcome_screen'}
    if session_id in session_histories:
        session_histories.pop(session_id, None)
    
    request.session['is_initial_load'] = True 

    config, created = ConfiguracaoGeral.objects.get_or_create(pk=1)
    
    context = {
        'config': config
    }
    return render(request, 'index.html', context)

def _go_to_main_menu(request, session_id):
    request.session['agendamento_state'] = {'step': 'initial'}
    session_histories.pop(session_id, None)
    response_payload = {
        'message': "Voltando ao menu principal. Como posso ajudar agora?",
        'buttons': [
            {'text': 'Agendar Serviço', 'value': 'start_booking'},
            {'text': 'Gerenciar Agendamentos', 'value': 'start_rebooking'}
        ]
    }
    get_session_history(session_id).append({"type": "ai", "content": response_payload['message']})
    return JsonResponse(response_payload)

@csrf_exempt
def chat_interaction(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message', '').strip()
            session_id = request.session.session_key
            if not session_id:
                return JsonResponse({'response': 'Erro de sessão.'}, status=400)

            history_list = get_session_history(session_id)

            agendamento_state = request.session.get('agendamento_state', {})
            if not agendamento_state or 'step' not in agendamento_state:
                agendamento_state = {'step': 'welcome_screen'}
                if not user_message and request.session.get('is_initial_load', True):
                    request.session['is_initial_load'] = False 
                    pass 

            response_payload = {'message': '', 'buttons': []}

            if user_message.lower() == 'reset':
                request.session['agendamento_state'] = {'step': 'welcome_screen'}
                session_histories.pop(session_id, None)
                response_payload['message'] = "Fluxo reiniciado. Clique em 'Iniciar' para começar."
                response_payload['buttons'] = [{'text': 'Iniciar', 'value': 'start_chat'}]
                history_list.append({"type": "human", "content": user_message})
                history_list.append({"type": "ai", "content": response_payload['message']})
                return JsonResponse(response_payload)

            if user_message.lower() == 'start_main_menu':
                history_list.append({"type": "human", "content": "Menu Principal"})
                return _go_to_main_menu(request, session_id)
            
            if user_message.lower() == 'start_booking' and agendamento_state.get('step') != 'waiting_for_service_selection':
                request.session['agendamento_state'] = {'step': 'initial'}
                agendamento_state = request.session.get('agendamento_state')
                session_histories.pop(session_id, None)
                agendamento_state['flow_type'] = 'new_booking'
                agendamento_state['step'] = 'waiting_for_service_selection'
                response_payload['message'] = "Ok, vamos começar um novo agendamento. Qual serviço você deseja agendar? Por favor, escolha uma opção abaixo:"
                services_data = services.get_servicos()
                buttons = []
                for s in services_data:
                    buttons.append({'text': f"{s['nome_servico']} (R${s['preco']:.2f})", 'value': str(s['id'])})
                response_payload['buttons'] = buttons
                history_list.append({"type": "human", "content": "Recomeçar Agendamento"})
                history_list.append({"type": "ai", "content": response_payload['message']})
                request.session['agendamento_state'] = agendamento_state
                return JsonResponse(response_payload)

            if not user_message and agendamento_state['step'] != 'welcome_screen':
                response_payload['message'] = "Por favor, digite sua resposta ou escolha uma opção de botão."
                if agendamento_state['step'] == 'waiting_for_phone_input' or agendamento_state['step'] == 'waiting_for_rebooking_phone':
                    response_payload['buttons'].append({'text': 'Tentar Novamente', 'value': 'yes_retry_phone'})
                history_list.append({"type": "human", "content": "(mensagem vazia)"}) 
                history_list.append({"type": "ai", "content": response_payload['message']})
                request.session['agendamento_state'] = agendamento_state
                return JsonResponse(response_payload)


            if agendamento_state['step'] == 'welcome_screen':
                if user_message.lower() == 'start_chat':
                    response_payload['message'] = "Olá! Como posso ajudar hoje? Escolha uma opção:"
                    response_payload['buttons'] = [
                        {'text': 'Agendar Serviço', 'value': 'start_booking'},
                        {'text': 'Gerenciar Agendamentos', 'value': 'start_rebooking'}
                    ]
                    agendamento_state['step'] = 'main_menu_choice'
                else:
                    response_payload['message'] = "Bem-vindo! Clique em 'Iniciar' para começar nosso atendimento."
                    response_payload['buttons'] = [{'text': 'Iniciar', 'value': 'start_chat'}]
                    agendamento_state['step'] = 'welcome_screen'

            elif agendamento_state['step'] == 'initial' or agendamento_state['step'] == 'main_menu_choice':
                if user_message.lower() == 'start_booking':
                    response_payload['message'] = "Ótimo! Qual serviço você deseja agendar? Por favor, escolha uma opção abaixo:"
                    services_data = services.get_servicos()
                    buttons = []
                    for s in services_data:
                        buttons.append({'text': f"{s['nome_servico']} (R${s['preco']:.2f})", 'value': str(s['id'])})
                    response_payload['buttons'] = buttons
                    agendamento_state['step'] = 'waiting_for_service_selection'
                    agendamento_state['flow_type'] = 'new_booking'
                elif user_message.lower() == 'start_rebooking':
                    response_payload['message'] = "Certo. Para gerenciar seus agendamentos, por favor, me informe seu telefone com DDD (somente números)."
                    response_payload['buttons'] = [] 
                    agendamento_state['step'] = 'waiting_for_rebooking_phone'
                    agendamento_state['flow_type'] = 'manage_appointments'
                else:
                    response_payload['message'] = "Olá! Como posso ajudar hoje? Escolha uma opção:"
                    response_payload['buttons'] = [
                        {'text': 'Agendar Serviço', 'value': 'start_booking'},
                        {'text': 'Gerenciar Agendamentos', 'value': 'start_rebooking'}
                    ]
                    agendamento_state['step'] = 'main_menu_choice'

            elif agendamento_state['step'] == 'waiting_for_service_selection':
                service_id_chosen = user_message.strip()
                if not service_id_chosen.isdigit():
                    response_payload['message'] = "Opção de serviço inválida. Por favor, escolha um serviço da lista de botões."
                    services_data = services.get_servicos()
                    buttons = []
                    for s in services_data:
                        buttons.append({'text': f"{s['nome_servico']} (R${s['preco']:.2f})", 'value': str(s['id'])})
                    response_payload['buttons'] = buttons
                    agendamento_state['step'] = 'waiting_for_service_selection'
                    request.session['agendamento_state'] = agendamento_state
                    return JsonResponse(response_payload)
                try:
                    servico_obj = Servico.objects.get(id=int(service_id_chosen))
                    agendamento_state['service_id'] = servico_obj.id
                    agendamento_state['service_name'] = servico_obj.nome_servico
                    agendamento_state['step'] = 'waiting_for_month_selection'
                    response_payload['message'] = f"Ótimo! Você escolheu '{servico_obj.nome_servico}'. Agora, para qual mês você deseja agendar?"
                    
                    today = timezone.localtime(timezone.now()).date()
                    months_buttons = []
                    
                    # --- TRADUÇÃO MANUAL DOS MESES (A CORREÇÃO ESTÁ AQUI) ---
                    MESES_PT = {
                        1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril",
                        5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto",
                        9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"
                    }

                    for i in range(3):
                        month_date = today + timedelta(days=30 * i)
                        first_day_of_month = date(month_date.year, month_date.month, 1)
                        
                        # Usa o dicionário para pegar o nome em Português
                        nome_mes = MESES_PT[first_day_of_month.month]
                        month_name = f"{nome_mes}/{first_day_of_month.year}"
                        
                        months_buttons.append({'text': month_name, 'value': first_day_of_month.strftime("%Y-%m")})
                    
                    response_payload['buttons'] = months_buttons
                except Servico.DoesNotExist:
                    response_payload['message'] = "Serviço inválido. Por favor, escolha um serviço da lista usando o ID do botão."
                    services_data = services.get_servicos()
                    buttons = []
                    for s in services_data:
                        buttons.append({'text': f"{s['nome_servico']} (R${s['preco']:.2f})", 'value': str(s['id'])})
                    response_payload['buttons'] = buttons
                    agendamento_state['step'] = 'waiting_for_service_selection'
                    request.session['agendamento_state'] = agendamento_state 
                    return JsonResponse(response_payload) 

            elif agendamento_state['step'] == 'waiting_for_month_selection':
                month_value_chosen = user_message.strip()
                try:
                    year, month = map(int, month_value_chosen.split('-'))
                    current_date = timezone.localtime(timezone.now()).date()
                    selected_month_date = date(year, month, 1)
                    if selected_month_date < date(current_date.year, current_date.month, 1):
                        response_payload['message'] = "Mês inválido. Por favor, escolha um mês futuro."
                        
                        # --- CORREÇÃO TAMBÉM NA RE-RENDERIZAÇÃO DOS BOTÕES ---
                        today = timezone.localtime(timezone.now()).date()
                        response_payload['buttons'] = []
                        MESES_PT = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
                        
                        for i in range(3):
                            month_date = today + timedelta(days=30 * i)
                            first_day_of_month = date(month_date.year, month_date.month, 1)
                            nome_mes = MESES_PT[first_day_of_month.month]
                            month_name = f"{nome_mes}/{first_day_of_month.year}"
                            response_payload['buttons'].append({'text': month_name, 'value': first_day_of_month.strftime("%Y-%m")})
                        
                        agendamento_state['step'] = 'waiting_for_month_selection'
                    else:
                        agendamento_state['month_selected'] = month_value_chosen
                        agendamento_state['step'] = 'waiting_for_day_selection'
                        
                        # Formata a data do mês escolhido para exibir na mensagem
                        MESES_PT = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
                        nome_mes_escolhido = MESES_PT[selected_month_date.month]
                        
                        response_payload['message'] = f"Certo! Para {nome_mes_escolhido}/{selected_month_date.year}, qual dia você deseja agendar? Escolha um dia válido:"
                        
                        days_buttons = []
                        num_days = (date(year, month + 1, 1) - date(year, month, 1)).days if month < 12 else (date(year + 1, 1, 1) - date(year, month, 1)).days
                        start_day_of_month = 1
                        if year == current_date.year and month == current_date.month:
                            start_day_of_month = current_date.day
                        for day in range(start_day_of_month, num_days + 1):
                            current_check_date = date(year, month, day)
                            if current_check_date.weekday() == 6: continue
                            if services.is_feriado(current_check_date): continue
                            days_buttons.append({'text': str(day), 'value': current_check_date.strftime("%Y-%m-%d")})
                        response_payload['buttons'] = days_buttons
                except ValueError:
                    response_payload['message'] = "Formato de mês inválido. Por favor, escolha um mês da lista de botões."
                    # Recria botões em caso de erro...
                    today = timezone.localtime(timezone.now()).date()
                    buttons = []
                    MESES_PT = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
                    for i in range(3):
                        month_date = today + timedelta(days=30 * i)
                        first_day_of_month = date(month_date.year, month_date.month, 1)
                        nome_mes = MESES_PT[first_day_of_month.month]
                        month_name = f"{nome_mes}/{first_day_of_month.year}"
                        buttons.append({'text': month_name, 'value': first_day_of_month.strftime("%Y-%m")})
                    response_payload['buttons'] = buttons
                    agendamento_state['step'] = 'waiting_for_month_selection'
                    request.session['agendamento_state'] = agendamento_state
                    return JsonResponse(response_payload)
            
            elif agendamento_state['step'] == 'waiting_for_day_selection':
                day_value_chosen = user_message.strip()
                try:
                    selected_date = datetime.strptime(day_value_chosen, "%Y-%m-%d").date()
                    agendamento_state['date_selected'] = selected_date.strftime("%Y-%m-%d")
                    
                    all_barbeiros = services.get_barbeiros()
                    available_barbeiros = []
                    
                    for b in all_barbeiros:
                        horarios_check = services.get_horarios_disponiveis(
                            agendamento_state['date_selected'],
                            agendamento_state['service_id'],
                            b['id'] 
                        )
                        if horarios_check.get('success') and horarios_check.get('horarios'):
                            available_barbeiros.append(b)

                    if not available_barbeiros:
                        response_payload['message'] = f"Desculpe, não há nenhum barbeiro com horários disponíveis para este serviço no dia {selected_date.strftime('%d/%m/%Y')}. Por favor, escolha outro dia."
                        agendamento_state['step'] = 'waiting_for_day_selection'
                        year, month = map(int, agendamento_state['month_selected'].split('-'))
                        current_date = timezone.localtime(timezone.now()).date()
                        days_buttons = []
                        num_days = (date(year, month + 1, 1) - date(year, month, 1)).days if month < 12 else (date(year + 1, 1, 1) - date(year, month, 1)).days
                        start_day_of_month = 1
                        if year == current_date.year and month == current_date.month:
                            start_day_of_month = current_date.day
                        for day in range(start_day_of_month, num_days + 1):
                            current_check_date = date(year, month, day)
                            if current_check_date.weekday() == 6: continue
                            if services.is_feriado(current_check_date): continue
                            days_buttons.append({'text': str(day), 'value': current_check_date.strftime("%Y-%m-%d")})
                        response_payload['buttons'] = days_buttons
                    else:
                        agendamento_state['step'] = 'waiting_for_barber_selection'
                        response_payload['message'] = f"Certo! Para {selected_date.strftime('%d/%m/%Y')}, estes são os barbeiros disponíveis. Qual você prefere?"
                        buttons = []
                        for b in available_barbeiros: 
                            buttons.append({'text': b['nome_completo'], 'value': str(b['id'])})
                        response_payload['buttons'] = buttons

                except ValueError:
                    response_payload['message'] = "Formato de dia inválido. Por favor, escolha um dia da lista de botões."
                    year, month = map(int, agendamento_state['month_selected'].split('-'))
                    current_date = timezone.localtime(timezone.now()).date()
                    days_buttons = []
                    num_days = (date(year, month + 1, 1) - date(year, month, 1)).days if month < 12 else (date(year + 1, 1, 1) - date(year, month, 1)).days
                    start_day_of_month = 1
                    if year == current_date.year and month == current_date.month:
                        start_day_of_month = current_date.day
                    for day in range(start_day_of_month, num_days + 1):
                        current_check_date = date(year, month, day)
                        if current_check_date.weekday() == 6: continue
                        if services.is_feriado(current_check_date): continue
                        days_buttons.append({'text': str(day), 'value': current_check_date.strftime("%Y-%m-%d")})
                    response_payload['buttons'] = days_buttons
                    agendamento_state['step'] = 'waiting_for_day_selection'
                    request.session['agendamento_state'] = agendamento_state
                    return JsonResponse(response_payload)

            elif agendamento_state['step'] == 'waiting_for_barber_selection':
                barber_id_chosen = user_message.strip()
                if not barber_id_chosen.isdigit():
                    response_payload['message'] = "Opção de barbeiro inválida. Por favor, escolha um barbeiro da lista de botões."
                    agendamento_state['step'] = 'waiting_for_barber_selection' 
                    request.session['agendamento_state'] = agendamento_state
                    return JsonResponse(response_payload)

                try:
                    barbeiro_obj = Barbeiro.objects.get(id=int(barber_id_chosen))
                    agendamento_state['barber_id'] = barbeiro_obj.id
                    agendamento_state['barber_name'] = barbeiro_obj.nome_completo
                    agendamento_state['step'] = 'waiting_for_time_selection'
                    
                    horarios_data = services.get_horarios_disponiveis(
                        agendamento_state['date_selected'],
                        agendamento_state['service_id'],
                        agendamento_state['barber_id']
                    )
                    
                    time_buttons = []
                    if horarios_data.get('success') and horarios_data.get('horarios'):
                        response_payload['message'] = f"Ótimo! Você escolheu '{barbeiro_obj.nome_completo}'. Agora, qual horário você deseja?"
                        for h in horarios_data['horarios']:
                            time_buttons.append({'text': h['hora_inicio'], 'value': h['hora_inicio']})
                    else:
                        response_payload['message'] = horarios_data.get('message', "Ocorreu um erro ao buscar os horários. Por favor, tente novamente.")
                        agendamento_state['step'] = 'main_menu_choice'
                        request.session['agendamento_state'] = agendamento_state
                        return JsonResponse(response_payload)

                    response_payload['buttons'].extend(time_buttons)

                except Barbeiro.DoesNotExist:
                    response_payload['message'] = "Barbeiro não encontrado. Por favor, escolha um barbeiro da lista."
                    agendamento_state['step'] = 'waiting_for_barber_selection'
                    request.session['agendamento_state'] = agendamento_state
                    return JsonResponse(response_payload)

            elif agendamento_state['step'] == 'waiting_for_time_selection':
                time_value_chosen = user_message.strip()
                if not re.match(r'^\d{2}:\d{2}$', time_value_chosen):
                    response_payload['message'] = "Horário inválido. Por favor, escolha um horário da lista de botões."
                    agendamento_state['step'] = 'waiting_for_time_selection'
                    request.session['agendamento_state'] = agendamento_state
                    return JsonResponse(response_payload)
                try:
                    datetime.strptime(time_value_chosen, '%H:%M').time()
                    agendamento_state['time_selected'] = time_value_chosen
                    agendamento_state['step'] = 'waiting_for_phone_input'
                    response_payload['message'] = f"Certo! Seu agendamento será em {datetime.strptime(agendamento_state['date_selected'], '%Y-%m-%d').strftime('%d/%m/%Y')} às {time_value_chosen}. Por favor, me informe APENAS seu telefone com DDD (somente números)."
                    response_payload['buttons'] = [] 
                    
                except ValueError:
                    response_payload['message'] = "Horário fora do range válido. Por favor, escolha um horário da lista de botões."
                    agendamento_state['step'] = 'waiting_for_time_selection'
                    request.session['agendamento_state'] = agendamento_state
                    return JsonResponse(response_payload)

            elif agendamento_state['step'] == 'waiting_for_phone_input':
                if user_message.lower() == 'yes_retry_phone':
                    response_payload['message'] = "Por favor, me informe APENAS seu telefone com DDD (somente números)."
                    response_payload['buttons'] = [] 
                    agendamento_state['step'] = 'waiting_for_phone_input'
                    return JsonResponse(response_payload)

                client_phone_input = re.sub(r'\D', '', user_message.strip())

                if not (client_phone_input and len(client_phone_input) >= 10):
                    response_payload['message'] = "Telefone inválido. Por favor, informe APENAS seu telefone com DDD (somente números)."
                    response_payload['buttons'] = [{'text': 'Tentar Novamente', 'value': 'yes_retry_phone'}]
                    agendamento_state['step'] = 'waiting_for_phone_input'
                    return JsonResponse(response_payload)

                agendamento_state['client_phone'] = client_phone_input
                client_lookup_json = services.find_cliente_by_telefone(client_phone_input)

                if client_lookup_json.get('success'):
                    agendamento_state['client_name_from_db'] = client_lookup_json['nome_completo']
                    if agendamento_state.get('flow_type') == 'manage_appointments':
                         agendamento_state['rebooking_client_id'] = client_lookup_json['id']
                    response_payload['message'] = f"Seu nome é '{agendamento_state['client_name_from_db']}'? Por favor, responda 'sim' ou 'não'."
                    response_payload['buttons'] = [{'text': 'Sim', 'value': 'sim_confirm_name'}, {'text': 'Não', 'value': 'nao_confirm_name'}]
                    agendamento_state['step'] = 'waiting_for_name_confirmation'
                else:
                    if agendamento_state.get('flow_type') == 'new_booking':
                        agendamento_state['step'] = 'waiting_for_new_client_name'
                        response_payload['message'] = "Não encontramos um cadastro com este telefone. Por favor, me informe seu nome completo."
                        response_payload['buttons'] = [] 
                    elif agendamento_state.get('flow_type') == 'manage_appointments':
                        response_payload['message'] = "Não encontramos nenhum agendamento ativo para este telefone. Deseja tentar novamente?"
                        response_payload['buttons'] = [{'text': 'Sim', 'value': 'yes_retry_phone'}, {'text': 'Não', 'value': 'start_main_menu'}]
                        agendamento_state['step'] = 'waiting_for_rebooking_phone'
                    else:
                        response_payload['message'] = "Ocorreu um erro no fluxo. Por favor, digite 'reset' para reiniciar."
                        response_payload['buttons'] = [{'text': 'Reset', 'value': 'reset'}]
                        agendamento_state['step'] = 'welcome_screen'

            elif agendamento_state['step'] == 'waiting_for_new_client_name':
                agendamento_state['client_name'] = user_message.strip()
                response_payload['message'] = f"Ok, {agendamento_state['client_name']}. Este será seu primeiro agendamento conosco. Vamos confirmar seu agendamento:\n" \
                                              f"Serviço: {agendamento_state['service_name']}\n" \
                                              f"Data: {datetime.strptime(agendamento_state['date_selected'], '%Y-%m-%d').strftime('%d/%m/%Y')}\n" \
                                              f"Horário: {agendamento_state['time_selected']}\n" \
                                              f"Barbeiro: {agendamento_state['barber_name']}\n" \
                                              f"Nome Cliente: {agendamento_state['client_name']}\n" \
                                              f"Telefone: {agendamento_state['client_phone']}\n\n" \
                                              "Está tudo correto? Responda com 'sim' para confirmar."
                response_payload['buttons'] = [{'text': 'Sim', 'value': 'sim_final_confirm'}, {'text': 'Não', 'value': 'nao_final_confirm'}]
                agendamento_state['step'] = 'waiting_for_final_confirmation'

            elif agendamento_state['step'] == 'waiting_for_name_confirmation':
                if user_message.lower() == 'sim_confirm_name' or user_message.lower() == 'sim':
                    agendamento_state['client_name'] = agendamento_state['client_name_from_db']
                    if agendamento_state.get('flow_type') == 'new_booking':
                        response_payload['message'] = f"Ok, {agendamento_state['client_name']}. Vamos confirmar seu agendamento:\n" \
                                                      f"Serviço: {agendamento_state['service_name']}\n" \
                                                      f"Data: {datetime.strptime(agendamento_state['date_selected'], '%Y-%m-%d').strftime('%d/%m/%Y')}\n" \
                                                      f"Horário: {agendamento_state['time_selected']}\n" \
                                                      f"Barbeiro: {agendamento_state['barber_name']}\n" \
                                                      f"Nome Cliente: {agendamento_state['client_name']}\n" \
                                                      f"Telefone: {agendamento_state['client_phone']}\n\n" \
                                                      "Está tudo correto? Responda com 'sim' para confirmar."
                        response_payload['buttons'] = [{'text': 'Sim', 'value': 'sim_final_confirm'}, {'text': 'Não', 'value': 'nao_final_confirm'}]
                        agendamento_state['step'] = 'waiting_for_final_confirmation'

                    elif agendamento_state.get('flow_type') == 'manage_appointments':
                        cliente_obj = Cliente.objects.get(id=agendamento_state['rebooking_client_id'])
                        agendamentos_cliente = Agendamento.objects.filter(
                            cliente=cliente_obj,
                            data_agendada__gte=timezone.localtime(timezone.now()).date(),
                            status__in=['pendente', 'confirmado']
                        ).order_by('data_agendada', 'hora_inicio').select_related('barbeiro', 'servico')

                        if agendamentos_cliente.exists():
                            response_message = f"Certo, {agendamento_state['client_name']}. Estes são seus agendamentos ativos:\n"
                            agendamento_state['current_appointments_list'] = {}
                            response_message += '<div class="agendamentos-list-chatbot">'
                            for idx, agendamento in enumerate(agendamentos_cliente):
                                agendamento_info = (
                                    f'<div class="agendamento-card">'
                                    f'  <div class="card-header"><strong>Agendamento #{idx+1}</strong></div>'
                                    f'  <div class="card-body">'
                                    f'    <p><strong>Serviço:</strong> {agendamento.servico.nome_servico}</p>'
                                    f'    <p><strong>Barbeiro:</strong> {agendamento.barbeiro.nome_completo}</p>'
                                    f'    <p><strong>Data:</strong> {agendamento.data_agendada.strftime('%d/%m/%Y')}</p>'
                                    f'    <p><strong>Horário:</strong> {agendamento.hora_inicio.strftime('%H:%M')}</p>'                                    
                                    f'    <p><strong>Status:</strong> <span class="status-badge {agendamento.status}">{agendamento.get_status_display()}</span></p>'
                                    f'  </div>'
                                    f'</div>'
                                )
                                response_message += agendamento_info
                                agendamento_state['current_appointments_list'][str(idx+1)] = agendamento.id
                            response_message += '</div>'
                            response_payload['message'] = response_message + "\nPor favor, digite o NÚMERO do agendamento que deseja gerenciar (ex: 1) ou escolha uma ação geral:"
                            response_payload['buttons'] = [
                                {'text': 'Confirmar Todos', 'value': 'confirm_all_appointments'},
                                {'text': 'Cancelar Todos', 'value': 'cancel_all_appointments'},
                            ]
                            agendamento_state['step'] = 'awaiting_specific_appointment_action_or_all'
                        else:
                            response_payload['message'] = "Você não possui agendamentos ativos. Deseja agendar um novo serviço?"
                            response_payload['buttons'] = [{'text': 'Agendar Serviço', 'value': 'start_booking'}]
                            agendamento_state['step'] = 'main_menu_choice'

                elif user_message.lower() == 'nao_confirm_name' or user_message.lower() == 'nao':
                    response_payload['message'] = "Ok. Qual o nome correto para este telefone?"
                    response_payload['buttons'] = [] 
                    agendamento_state['step'] = 'waiting_for_correct_name'
                else:
                    response_payload['message'] = "Resposta inválida. Por favor, responda 'Sim' ou 'Não'."
                    response_payload['buttons'] = [{'text': 'Sim', 'value': 'sim_confirm_name'}, {'text': 'Não', 'value': 'nao_confirm_name'}]
                    agendamento_state['step'] = 'waiting_for_name_confirmation'

            elif agendamento_state['step'] == 'waiting_for_correct_name':
                agendamento_state['client_name'] = user_message.strip()
                try:
                    cliente_obj = Cliente.objects.get(telefone=agendamento_state['client_phone'])
                    cliente_obj.nome_completo = agendamento_state['client_name']
                    cliente_obj.save()
                except Cliente.DoesNotExist:
                    pass 

                if agendamento_state.get('flow_type') == 'new_booking':
                    response_payload['message'] = f"Ok, usaremos {agendamento_state['client_name']}. Vamos confirmar seu agendamento:\n" \
                                                  f"Serviço: {agendamento_state['service_name']}\n" \
                                                  f"Data: {datetime.strptime(agendamento_state['date_selected'], '%Y-%m-%d').strftime('%d/%m/%Y')}\n" \
                                                  f"Horário: {agendamento_state['time_selected']}\n" \
                                                  f"Barbeiro: {agendamento_state['barber_name']}\n" \
                                                  f"Nome Cliente: {agendamento_state['client_name']}\n" \
                                                  f"Telefone: {agendamento_state['client_phone']}\n\n" \
                                                  "Está tudo correto? Responda com 'sim' para confirmar."
                    response_payload['buttons'] = [{'text': 'Sim', 'value': 'sim_final_confirm'}, {'text': 'Não', 'value': 'nao_final_confirm'}]
                    agendamento_state['step'] = 'waiting_for_final_confirmation'

                elif agendamento_state.get('flow_type') == 'manage_appointments':
                    cliente_obj = Cliente.objects.get(id=agendamento_state['rebooking_client_id'])
                    agendamentos_cliente = Agendamento.objects.filter(
                        cliente=cliente_obj,
                        data_agendada__gte=timezone.localtime(timezone.now()).date(),
                        status__in=['pendente', 'confirmado']
                    ).order_by('data_agendada', 'hora_inicio').select_related('barbeiro', 'servico')
                    if agendamentos_cliente.exists():
                        response_message = f"Certo, {agendamento_state['client_name']}. Seu nome foi atualizado. Estes são seus agendamentos ativos:\n"
                        agendamento_state['current_appointments_list'] = {}
                        for idx, agendamento in enumerate(agendamentos_cliente):
                            agendamento_info = f"{idx+1}. {agendamento.servico.nome_servico}..."
                            response_message += f"- {agendamento_info}\n"
                            agendamento_state['current_appointments_list'][str(idx+1)] = agendamento.id
                        response_payload['message'] = response_message + "\nPor favor, digite o NÚMERO do agendamento que deseja gerenciar (ex: 1) ou escolha uma ação geral:"
                        response_payload['buttons'] = [
                            {'text': 'Confirmar Todos', 'value': 'confirm_all_appointments'},
                            {'text': 'Cancelar Todos', 'value': 'cancel_all_appointments'},
                        ]
                        agendamento_state['step'] = 'awaiting_specific_appointment_action_or_all'
                    else:
                        response_payload['message'] = "Você não possui agendamentos ativos. Deseja agendar um novo serviço?"
                        response_payload['buttons'] = [{'text': 'Agendar Serviço', 'value': 'start_booking'}]
                        agendamento_state['step'] = 'main_menu_choice'
                else: 
                    response_payload['message'] = "Erro de fluxo. Por favor, reinicie. Confirme seu agendamento:"
                    response_payload['buttons'] = [{'text': 'Sim', 'value': 'sim_final_confirm'}, {'text': 'Não', 'value': 'nao_final_confirm'}]
                    agendamento_state['step'] = 'waiting_for_final_confirmation'

            elif agendamento_state['step'] == 'waiting_for_final_confirmation':
                if user_message.lower() == 'sim_final_confirm' or user_message.lower() == 'sim':
                    print(f"DEBUG CHATBOT_GUIADO: Confirmacao final 'sim'. Tentando salvar agendamento. Current state: {agendamento_state}")
                    
                    # ===== CHAMADA DE AGENDAMENTO =====
                    save_result = services.criar_agendamento(
                        nome_cliente=agendamento_state['client_name'],
                        telefone_cliente=agendamento_state['client_phone'],
                        servico_id=agendamento_state['service_id'],
                        data_agendada_str=agendamento_state['date_selected'],
                        hora_inicio_str=agendamento_state['time_selected'],
                        barbeiro_id=agendamento_state['barber_id']
                    )
                    
                    if save_result["success"]:
                        response_payload['message'] = f"Agendamento confirmado! {save_result['message']}"
                        response_payload['buttons'] = [{'text': 'Agendar Novo Serviço', 'value': 'start_booking'}]
                        agendamento_state['step'] = 'main_menu_choice' 
                        session_histories.pop(session_id, None) 
                        print(f"DEBUG CHATBOT_GUIADO: Agendamento salvo com sucesso: {save_result['agendamento_id']}")
                    else:
                        response_payload['message'] = f"Desculpe, ocorreu um erro ao agendar: {save_result['message']}. Por favor, clique em 'Agendar Novo Serviço'."
                        response_payload['buttons'] = [{'text': 'Agendar Novo Serviço', 'value': 'start_booking'}]
                        agendamento_state['step'] = 'initial'
                        session_histories.pop(session_id, None)
                        print(f"DEBUG CHATBOT_GUIADO: Falha ao salvar agendamento: {save_result['message']}")
                
                elif user_message.lower() == 'nao_final_confirm' or user_message.lower() == 'nao':
                    response_payload['message'] = "Agendamento não confirmado. Como posso ajudar agora?"
                    response_payload['buttons'] = [
                        {'text': 'Agendar Serviço', 'value': 'start_booking'},
                        {'text': 'Gerenciar Agendamentos', 'value': 'start_rebooking'}
                    ]
                    request.session['agendamento_state'] = {'step': 'main_menu_choice'}
                    session_histories.pop(session_id, None)
                else:
                    response_payload['message'] = "Agendamento não confirmado. Por favor, responda com 'sim' para confirmar, ou 'não' para recomeçar."
                    response_payload['buttons'] = [{'text': 'Sim', 'value': 'sim_final_confirm'}, {'text': 'Não', 'value': 'nao_final_confirm'}]
                    agendamento_state['step'] = 'waiting_for_final_confirmation'

            elif agendamento_state['step'] == 'waiting_for_rebooking_phone':
                if user_message.lower() == 'yes_retry_phone':
                    response_payload['message'] = "Por favor, me informe APENAS seu telefone com DDD (somente números)."
                    response_payload['buttons'] = [] 
                    agendamento_state['step'] = 'waiting_for_rebooking_phone'
                    return JsonResponse(response_payload)

                client_phone_input = re.sub(r'\D', '', user_message.strip())

                if not (client_phone_input and len(client_phone_input) >= 10):
                    response_payload['message'] = "Telefone inválido para gerenciamento. Por favor, informe APENAS seu telefone com DDD (somente números)."
                    response_payload['buttons'] = [{'text': 'Tentar Novamente', 'value': 'yes_retry_phone'}]
                    agendamento_state['step'] = 'waiting_for_rebooking_phone'
                    return JsonResponse(response_payload)

                agendamento_state['client_phone'] = client_phone_input
                client_lookup_json = services.find_cliente_by_telefone(client_phone_input)

                if client_lookup_json.get('success'):
                    agendamento_state['client_name_from_db'] = client_lookup_json['nome_completo']
                    if agendamento_state.get('flow_type') == 'manage_appointments':
                         agendamento_state['rebooking_client_id'] = client_lookup_json['id']
                    response_payload['message'] = f"Seu nome é '{agendamento_state['client_name_from_db']}'? Por favor, responda 'sim' ou 'não'."
                    response_payload['buttons'] = [{'text': 'Sim', 'value': 'sim_confirm_name'}, {'text': 'Não', 'value': 'nao_confirm_name'}]
                    agendamento_state['step'] = 'waiting_for_name_confirmation'
                else:
                    response_payload['message'] = "Não encontramos nenhum agendamento ativo para este telefone. Deseja tentar novamente?"
                    response_payload['buttons'] = [{'text': 'Sim', 'value': 'yes_retry_phone'}, {'text': 'Não', 'value': 'start_main_menu'}]
                    agendamento_state['step'] = 'waiting_for_rebooking_phone'

            elif agendamento_state['step'] == 'awaiting_specific_appointment_action_or_all':
                if user_message.lower() == 'confirm_all_appointments':
                    cliente_obj = Cliente.objects.get(id=agendamento_state['rebooking_client_id'])
                    updated_count = Agendamento.objects.filter(
                        cliente=cliente_obj,
                        data_agendada__gte=timezone.localtime(timezone.now()).date(),
                        status='pendente'
                    ).update(status='confirmado')
                    response_payload['message'] = f"{updated_count} agendamento(s) confirmado(s) com sucesso!"
                    response_payload['buttons'] = [{'text': 'Agendar Novo Serviço', 'value': 'start_booking'}]
                    request.session['agendamento_state'] = {'step': 'main_menu_choice'} 
                    session_histories.pop(session_id, None) 
                    return JsonResponse(response_payload) 

                elif user_message.lower() == 'cancel_all_appointments':
                    cliente_obj = Cliente.objects.get(id=agendamento_state['rebooking_client_id'])
                    updated_count = Agendamento.objects.filter(
                        cliente=cliente_obj,
                        data_agendada__gte=timezone.localtime(timezone.now()).date(),
                        status__in=['pendente', 'confirmado']
                    ).update(status='cancelado')
                    response_payload['message'] = f"{updated_count} agendamento(s) cancelado(s) com sucesso!"
                    response_payload['buttons'] = [{'text': 'Agendar Novo Serviço', 'value': 'start_booking'}]
                    request.session['agendamento_state'] = {'step': 'main_menu_choice'} 
                    session_histories.pop(session_id, None) 
                    return JsonResponse(response_payload) 

                elif user_message.isdigit():
                    appointment_idx = user_message.strip()
                    agendamento_id = agendamento_state.get('current_appointments_list', {}).get(appointment_idx)

                    if agendamento_id:
                        agendamento_to_act = Agendamento.objects.get(id=agendamento_id)
                        agendamento_state['current_agendamento_id_for_action'] = agendamento_id
                        response_payload['message'] = (
                            f"Você selecionou o agendamento:\n"
                            f"- {agendamento_to_act.servico.nome_servico} com {agendamento_to_act.barbeiro.nome_completo} "
                            f"em {agendamento_to_act.data_agendada.strftime('%d/%m/%Y')} às {agendamento_to_act.hora_inicio.strftime('%H:%M')}\n\n"
                            "O que deseja fazer com ele?"
                        )
                        response_payload['buttons'] = [
                            {'text': 'Confirmar', 'value': 'confirm_selected_appointment'},
                            {'text': 'Cancelar', 'value': 'cancel_selected_appointment'},
                            {'text': 'Cancelar e Reagendar', 'value': 'rebook_selected_appointment'},
                        ]
                        agendamento_state['step'] = 'confirm_cancel_rebook_choice'
                    else:
                        response_payload['message'] = "Número de agendamento inválido. Por favor, digite um número da lista ou escolha uma ação geral."
                        response_payload['buttons'] = [
                            {'text': 'Confirmar Todos', 'value': 'confirm_all_appointments'},
                            {'text': 'Cancelar Todos', 'value': 'cancel_all_appointments'},
                        ]
                        agendamento_state['step'] = 'awaiting_specific_appointment_action_or_all'
                else:
                    response_payload['message'] = "Opção inválida. Por favor, digite o número do agendamento ou escolha uma ação geral."
                    response_payload['buttons'] = [
                        {'text': 'Confirmar Todos', 'value': 'confirm_all_appointments'},
                        {'text': 'Cancelar Todos', 'value': 'cancel_all_appointments'},
                    ]
                    agendamento_state['step'] = 'awaiting_specific_appointment_action_or_all'

            elif agendamento_state['step'] == 'confirm_cancel_rebook_choice':
                agendamento_id = agendamento_state.get('current_agendamento_id_for_action')
                if not agendamento_id:
                    response_payload['message'] = "Ocorreu um erro. Por favor, reinicie o fluxo digitando 'reset'."
                    response_payload['buttons'] = []
                    request.session['agendamento_state'] = {'step': 'initial'}
                    session_histories.pop(session_id, None)
                    return JsonResponse(response_payload)

                try:
                    agendamento_obj = Agendamento.objects.get(id=agendamento_id)
                except Agendamento.DoesNotExist:
                    response_payload['message'] = "Agendamento não encontrado. Por favor, reinicie o fluxo digitando 'reset'."
                    response_payload['buttons'] = []
                    request.session['agendamento_state'] = {'step': 'initial'}
                    session_histories.pop(session_id, None)
                    return JsonResponse(response_payload)

                if user_message.lower() == 'confirm_selected_appointment':
                    agendamento_obj.status = 'confirmado'
                    agendamento_obj.save()
                    response_payload['message'] = "Agendamento confirmado com sucesso! Aguardamos você."
                    response_payload['buttons'] = [{'text': 'Agendar Novo Serviço', 'value': 'start_booking'}]
                    request.session['agendamento_state'] = {'step': 'main_menu_choice'}
                    session_histories.pop(session_id, None)
                elif user_message.lower() == 'cancel_selected_appointment':
                    agendamento_obj.status = 'cancelado'
                    agendamento_obj.save()
                    response_payload['message'] = ("Seu agendamento foi cancelado com sucesso!\n\n"
                                                   "Se quiser reagendar, clique em 'Agendar Serviço'.")
                    response_payload['buttons'] = [{'text': 'Agendar Serviço', 'value': 'start_booking'}]
                    request.session['agendamento_state'] = {'step': 'main_menu_choice'}
                    session_histories.pop(session_id, None)
                elif user_message.lower() == 'rebook_selected_appointment':
                    agendamento_obj.status = 'cancelado'
                    agendamento_obj.save()
                    agendamento_state['original_rebooked_appointment_id'] = agendamento_id
                    agendamento_state['service_id'] = agendamento_obj.servico.id
                    agendamento_state['service_name'] = agendamento_obj.servico.nome_servico
                    agendamento_state['barber_id'] = agendamento_obj.barbeiro.id
                    agendamento_state['barber_name'] = agendamento_obj.barbeiro.nome_completo
                    agendamento_state['client_phone'] = agendamento_obj.cliente.telefone
                    agendamento_state['client_name'] = agendamento_obj.cliente.nome_completo
                    response_payload['message'] = (f"Ok, o agendamento original foi cancelado. "
                                                   f"Vamos reagendar '{agendamento_state['service_name']}' com '{agendamento_state['barber_name']}'. "
                                                   "Para qual mês você deseja agendar?")
                    today = timezone.localtime(timezone.now()).date()
                    months_buttons = []
                    MESES_PT = {1: "Janeiro", 2: "Fevereiro", 3: "Março", 4: "Abril", 5: "Maio", 6: "Junho", 7: "Julho", 8: "Agosto", 9: "Setembro", 10: "Outubro", 11: "Novembro", 12: "Dezembro"}
                    for i in range(3):
                        month_date = today + timedelta(days=30 * i)
                        first_day_of_month = date(month_date.year, month_date.month, 1)
                        nome_mes = MESES_PT[first_day_of_month.month]
                        month_name = f"{nome_mes}/{first_day_of_month.year}"
                        months_buttons.append({'text': month_name, 'value': first_day_of_month.strftime("%Y-%m")})
                    response_payload['buttons'] = months_buttons
                    agendamento_state['step'] = 'waiting_for_month_selection'
                else:
                    response_payload['message'] = "Opção inválida. Por favor, escolha uma das opções de ação para o agendamento."
                    response_payload['buttons'] = [
                        {'text': 'Confirmar', 'value': 'confirm_selected_appointment'},
                        {'text': 'Cancelar', 'value': 'cancel_selected_appointment'},
                        {'text': 'Cancelar e Reagendar', 'value': 'rebook_selected_appointment'},
                    ]
                    agendamento_state['step'] = 'confirm_cancel_rebook_choice'

            request.session['agendamento_state'] = agendamento_state

            final_user_message_for_history = data.get('message', '').strip()
            if agendamento_state['step'] != 'welcome_screen' or final_user_message_for_history:
                history_list.append({"type": "human", "content": final_user_message_for_history})
            history_list.append({"type": "ai", "content": response_payload['message']})

            return JsonResponse(response_payload)

        except Exception as e:
            traceback.print_exc()
            return JsonResponse({"message": "Desculpe, ocorreu um erro crítico no servidor. Por favor, digite 'reset' para reiniciar.", "buttons": [{'text': 'Reset', 'value': 'reset'}]}, status=500)
    return HttpResponse("Método não permitido.", status=405)

@csrf_exempt
def twilio_whatsapp_webhook(request):
    if request.method == 'POST':
        from_number_whatsapp = request.POST.get('From', '')
        sms_body = request.POST.get('Body', '').strip().lower()
        button_payload = request.POST.get('ButtonPayload', '').strip().lower()

        resp = MessagingResponse()
        client_response = button_payload if button_payload else sms_body
        telefone_limpo_origem = re.sub(r'^\D*\+', '', from_number_whatsapp)
        telefone_limpo_origem = re.sub(r'\D', '', telefone_limpo_origem)

        try:
            cliente = Cliente.objects.get(telefone=telefone_limpo_origem)
            agendamento = Agendamento.objects.filter(
                cliente=cliente,
                data_agendada__gte=timezone.localtime(timezone.now()).date(),
                status__in=['pendente', 'confirmado']
            ).order_by('data_agendada', 'hora_inicio').first()

            if not agendamento:
                resp.message("Nao encontramos um agendamento ativo ou pendente para seu numero. Para agendar, acesse: [LINK_DO_SEU_CHATBOT_AQUI]")
                return HttpResponse(str(resp), content_type="text/xml")

            if client_response == '1' or client_response == 'confirmar':
                agendamento.status = 'confirmado'
                agendamento.save()
                resp.message("Seu agendamento foi confirmado com sucesso! Te aguardamos na Barbearia A Tesoura de Ouro.")
            elif client_response == '2' or client_response == 'cancelar':
                agendamento.status = 'cancelado'
                agendamento.save()
                resp.message("Seu agendamento foi cancelado com sucesso. Esperamos ve-lo(a) em breve!")
            elif client_response == '3' or client_response == 'reagendar':
                chat_reagendar_link = "https://seusite.onrender.com/chat/" 
                resp.message(f"Para reagendar seu horario, acesse nosso chatbot: {chat_reagendar_link}")
            else:
                resp.message("Desculpe, nao entendi sua resposta. Por favor, use as opcoes disponiveis no lembrete (se houver) ou digite '1' para confirmar, '2' para cancelar ou '3' para reagendar.")
        except Cliente.DoesNotExist:
            resp.message("Seu numero nao esta cadastrado em nosso sistema. Para agendar, acesse: [LINK_DO_SEU_CHATBOT_AQUI]")
        except Exception as e:
            print(f"DEBUG_WHATSAPP_WEBHOOK: Erro ao processar webhook WhatsApp para {from_number_whatsapp}: {e}")
            traceback.print_exc()
            resp.message("Ocorreu um erro ao processar sua solicitacao. Tente novamente ou entre em contato com a barbearia.")

        return HttpResponse(str(resp), content_type="text/xml")
    return HttpResponse("Método não permitido.", status=405)


@login_required
@user_passes_test(is_gerente, login_url='/accounts/login/')
def painel_atendimento(request):
    # 1. Carrega a Configuração (Logo e Nome)
    config, created = ConfiguracaoGeral.objects.get_or_create(pk=1)

    selected_date_str = request.GET.get('data')
    selected_barbeiro_id = request.GET.get('barbeiro')
    view_type = request.GET.get('view', 'daily')
    selected_status = request.GET.get('status', 'confirmado_pendente')

    hoje = timezone.localtime(timezone.now()).date()

    if selected_date_str:
        try:
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            selected_date = hoje
    else:
        selected_date = hoje

    previous_day = selected_date - timedelta(days=1)
    next_day = selected_date + timedelta(days=1)
    start_of_week = selected_date - timedelta(days=selected_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    previous_week = start_of_week - timedelta(weeks=1)
    next_week = start_of_week + timedelta(weeks=1)

    barbeiros = Barbeiro.objects.all().order_by('nome_completo')

    if view_type == 'weekly':
        agendamentos_query = Agendamento.objects.filter(data_agendada__range=[start_of_week, end_of_week])
    else:
        agendamentos_query = Agendamento.objects.filter(data_agendada=selected_date)

    if selected_status == 'confirmado_pendente':
        agendamentos_query = agendamentos_query.filter(status__in=['confirmado', 'pendente'])
    elif selected_status == 'realizado':
        agendamentos_query = agendamentos_query.filter(status='realizado')
    elif selected_status == 'cancelado':
        agendamentos_query = agendamentos_query.filter(status='cancelado')
    elif selected_status == 'todos':
        pass
    else:
        agendamentos_query = agendamentos_query.filter(status__in=['confirmado', 'pendente'])

    if selected_barbeiro_id and selected_barbeiro_id.isdigit():
        agendamentos_query = agendamentos_query.filter(barbeiro_id=int(selected_barbeiro_id))

    agendamentos = agendamentos_query.order_by('data_agendada', 'hora_inicio')

    agendamentos_por_dia = {}
    current_day_iter_for_dict = start_of_week
    while current_day_iter_for_dict <= end_of_week:
        agendamentos_por_dia[current_day_iter_for_dict] = []
        current_day_iter_for_dict += timedelta(days=1)

    for agendamento in agendamentos:
        if agendamento.data_agendada in agendamentos_por_dia:
            agendamentos_por_dia[agendamento.data_agendada].append(agendamento)
        else:
            agendamentos_por_dia[agendamento.data_agendada] = [agendamento]

    for day, appts in agendamentos_por_dia.items():
        agendamentos_por_dia[day] = sorted(appts, key=lambda x: x.hora_inicio)

    week_days_list = []
    current_day_for_template = start_of_week
    while current_day_for_template <= end_of_week:
        week_days_list.append(current_day_for_template)
        current_day_for_template += timedelta(days=1)

    status_options = [
        {'value': 'confirmado_pendente', 'label': 'Confirmados e Pendentes'},
        {'value': 'realizado', 'label': 'Realizados'},
        {'value': 'cancelado', 'label': 'Cancelados'},
        {'value': 'todos', 'label': 'Todos os Status'},
    ]

    context = {
        'config': config,  # <--- AQUI ESTÁ A MÁGICA
        'agendamentos': agendamentos,
        'agendamentos_por_dia': agendamentos_por_dia,
        'data_hoje': hoje,
        'selected_date': selected_date,
        'previous_day': previous_day,
        'next_day': next_day,
        'barbeiros': barbeiros,
        'selected_barbeiro_id': int(selected_barbeiro_id) if selected_barbeiro_id and selected_barbeiro_id.isdigit() else '',
        'view_type': view_type,
        'start_of_week': start_of_week,
        'end_of_week': end_of_week,
        'previous_week': previous_week,
        'next_week': next_week,
        'week_days_list': week_days_list,
        'status_options': status_options,
        'selected_status': selected_status,
    }
    return render(request, 'painel_atendimento.html', context)

@login_required
@user_passes_test(is_gerente, login_url='/accounts/login/')
def dashboard_visao_geral(request):
    # Carrega a configuração (para o header)
    config, _ = ConfiguracaoGeral.objects.get_or_create(pk=1)
    
    # Esta view apenas carrega a "casca" da página
    context = {
        'config': config,
        'page_title': 'Visão Geral' # Para o título da página
    }
    return render(request, 'dashboard_visao_geral.html', context)