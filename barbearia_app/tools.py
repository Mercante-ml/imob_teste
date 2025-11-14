# barbearia_app/tools.py (VERSÃO SIMPLIFICADA SEM @tool PARA CHATBOT DE BOTÕES)

import json
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
# from langchain.tools import tool # Removido, nao é mais uma tool do LangChain
from . import services # Importa o módulo services


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal): return float(obj)
        return super(DecimalEncoder, self).default(obj)

# Estas funções são agora APENAS funções Python, não ferramentas do LangChain.
# O views.py vai chamá-las diretamente de services.py.

def find_cliente_by_telefone(telefone: str) -> str: # Remover @tool aqui e em outras
    """
    Verifica se um cliente existe no sistema dado um número de telefone.
    Retorna um JSON com {"success": True, "nome_completo": "Nome do Cliente", "id": cliente.id}
    ou {"success": False, "message": "Cliente não encontrado."}.
    """
    return json.dumps(services.find_cliente_by_telefone(telefone))

def find_barbeiro_by_name(nome_barbeiro: str) -> str:
    """
    Busca um barbeiro pelo nome completo (ou parte do nome) e retorna seu ID e nome.
    Útil para o agente converter o nome dado pelo usuário em um ID numérico.
    """
    nome_barbeiro_lower = nome_barbeiro.lower().strip()
    try:
        barbeiro = services.Barbeiro.objects.get(nome_completo__iexact=nome_barbeiro_lower)
        return json.dumps({"success": True, "barbeiro_id": barbeiro.id, "nome_completo": barbeiro.nome_completo})
    except services.Barbeiro.DoesNotExist:
        barbeiros_parcial = services.Barbeiro.objects.filter(nome_completo__icontains=nome_barbeiro_lower)
        if barbeiros_parcial.count() == 1:
            barbeiro = barbeiros_parcial.first()
            return json.dumps({"success": False, "message": "Multiplos barbeiros encontrados com esse nome. Seja mais específico.", "found_barbeiros": [b.nome_completo for b in barbeiros_parcial]})
        else:
            return json.dumps({"success": False, "message": "Barbeiro não encontrado."})

def find_service_by_id_or_name(query: str) -> str:
    """Busca e valida a escolha de serviço do usuário pelo ID ou nome."""
    query = query.strip().lower()
    servico = None
    if query.isdigit():
        try: servico = services.Servico.objects.get(id=int(query))
        except services.Servico.DoesNotExist: pass
    else:
        try: servico = services.Servico.objects.get(nome_servico__iexact=query)
        except services.Servico.DoesNotExist:
            query_words = set(query.split())
            for s in services.Servico.objects.all():
                if query_words.intersection(set(s.nome_servico.lower().split())):
                    servico = s; break
    if servico: return json.dumps({"status": "success", "servico": {"id": servico.id, "nome": servico.nome_servico}})
    else: return json.dumps({"status": "not_found"})

def converter_data_relativa_para_absoluta(texto_data: str) -> str:
    """Converte datas como 'amanhã' ou 'próxima segunda' para o formato AAAA-MM-DD."""
    data_resolvida = services._resolve_date(texto_data)
    if data_resolvida:
        return data_resolvida.strftime('%Y-%m-%d')
    return f"erro: não foi possível entender a data '{texto_data}'."

def listar_servicos() -> str:
    """Lista todos os serviços, retornando uma string já formatada."""
    servicos_list = services.get_servicos()
    if not servicos_list: return "No momento, não temos serviços cadastrados."
    lista_texto = ["Certo! Nossos serviços são:"]
    for s in servicos_list:
        preco_formatado = f"R$ {s['preco']:.2f}".replace('.', ',')
        lista_texto.append(f"ID {s['id']}: {s['nome_servico']} ({s['duracao_minutos']} min - {preco_formatado})")
    return "\n".join(lista_texto)

def listar_barbeiros() -> str:
    """Lista todos os barbeiros, retornando uma string já formatada."""
    barbeiros_list = services.get_barbeiros()
    if not barbeiros_list: return "Não temos barbeiros cadastrados no momento."
    lista_texto = ["Estes são nossos profissionais:"]
    for b in barbeiros_list:
        especialidade = f" - Especialidade: {b['especialidade']}" if b['especialidade'] else ""
        lista_texto.append(f"ID {b['id']}: {b['nome_completo']}{especialidade}")
    return "\n".join(lista_texto)

def verificar_horarios_disponiveis(data_agendada: str, servico_id: int, barbeiro_id: int = None) -> str:
    """Verifica os horários disponíveis. O ID do barbeiro é opcional."""
    return json.dumps(services.get_horarios_disponiveis(data_agendada, servico_id, barbeiro_id))

def agendar_servico_completo(nome_cliente: str, telefone_cliente: str, servico_id: int, data_agendada: str, hora_inicio: str, barbeiro_id: int) -> str:
    """Agenda um serviço completo. Requer todos os dados."""
    return json.dumps(services.criar_agendamento(nome_cliente, telefone_cliente, servico_id, data_agendada, hora_inicio, barbeiro_id))

# tools_list = [] # Removido, pois nao há mais tools do LangChain