# populate_test_agendamentos.py
import os
import django
import random
from datetime import datetime, timedelta, date, time
from django.utils import timezone

# 1. Configura o ambiente Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_projeto.settings')
django.setup()

# 2. Importa os modelos (DEPOIS do setup)
from barbearia_app.models import Agendamento, Barbeiro, Servico, Cliente
from django.db import transaction

# --- CONFIGURAÇÕES DA SIMULAÇÃO ---
NUMERO_DE_AGENDAMENTOS = 100
DIAS_PARA_TRAS = 30 # Gerar dados de 30 dias atrás...
DIAS_PARA_FRENTE = 30 # ...até 30 dias no futuro.

HORA_ABERTURA = 9  # 9h
HORA_FECHAMENTO = 17 # 17h (para evitar agendamentos que terminam depois das 18h)
# ----------------------------------

def run_simulation():
    print("Iniciando simulação... Buscando barbeiros e serviços...")
    
    # 3. Pega os "ingredientes" (Barbeiros e Serviços)
    barbeiros = list(Barbeiro.objects.all())
    servicos = list(Servico.objects.all())

    if not barbeiros or not servicos:
        print("\n[ERRO FATAL]")
        print("Você precisa rodar 'populate_core.py' primeiro.")
        print("O banco de dados não tem barbeiros ou serviços para simular.")
        return

    print(f"Encontrados {len(barbeiros)} barbeiros e {len(servicos)} serviços.")
    
    print(f"Agendamentos antes da simulação: {Agendamento.objects.count()}")

    agendamentos_criados = 0
    tentativas = 0

    print(f"Tentando criar {NUMERO_DE_AGENDAMENTOS} agendamentos de teste...")

    # 4. O Loop de Geração
    while agendamentos_criados < NUMERO_DE_AGENDAMENTOS and tentativas < (NUMERO_DE_AGENDAMENTOS * 2):
        tentativas += 1 # Para evitar loop infinito se a agenda lotar

        # Escolhe ingredientes aleatórios
        barbeiro = random.choice(barbeiros)
        servico = random.choice(servicos)

        # Cria um cliente falso único
        cliente_fake_nome = f"Cliente Simulado {agendamentos_criados}"
        cliente_fake_telefone = f"99999{agendamentos_criados:04}" # Ex: 999990001
        cliente, _ = Cliente.objects.get_or_create(
            telefone=cliente_fake_telefone,
            defaults={'nome_completo': cliente_fake_nome}
        )

        # Gera data aleatória (passado e futuro)
        dias_offset = random.randint(-DIAS_PARA_TRAS, DIAS_PARA_FRENTE)
        data_agendada = timezone.now().date() + timedelta(days=dias_offset)

        # Pula Sábados e Domingos (simplificação)
        if data_agendada.weekday() >= 5:
            continue

        # Gera hora aleatória (na grade de 30 min)
        hora_agendada = time(random.randint(HORA_ABERTURA, HORA_FECHAMENTO), random.choice([0, 30]))

        # Define o status baseado na data
        if data_agendada < timezone.now().date():
            status = random.choice(['realizado', 'cancelado']) # Passado
        else:
            status = random.choice(['pendente', 'confirmado']) # Futuro

        # Validação: Checa se o horário está vago (evita "double booking")
        hora_fim_calculada = (datetime.combine(data_agendada, hora_agendada) + timedelta(minutes=servico.duracao_minutos)).time()

        conflito = Agendamento.objects.filter(
            barbeiro=barbeiro,
            data_agendada=data_agendada,
            hora_inicio__lt=hora_fim_calculada, # Início < Fim do novo
            hora_fim__gt=hora_agendada        # Fim > Início do novo
        ).exists()

        if conflito:
            #print(f"Conflito! Pulando {data_agendada} @ {hora_agendada} para {barbeiro.nome_completo}")
            continue # Pula para a próxima tentativa

        # 5. Cria o Agendamento
        # O 'save()' do models.py vai calcular 'hora_fim' e 'valor_historico' sozinho!
        with transaction.atomic():
            Agendamento.objects.create(
                cliente=cliente,
                barbeiro=barbeiro,
                servico=servico,
                data_agendada=data_agendada,
                hora_inicio=hora_agendada,
                status=status
            )

        agendamentos_criados += 1
        print(f"  [{agendamentos_criados}/{NUMERO_DE_AGENDAMENTOS}] Agendamento criado: {data_agendada} @ {hora_agendada} ({status})")

    print(f"\nSimulação concluída. {agendamentos_criados} agendamentos criados.")
    print(f"Agendamentos após a simulação: {Agendamento.objects.count()}")


if __name__ == '__main__':
    run_simulation()