# populate_core.py (ATUALIZADO COM A REGRA DE 30/60/90 MINUTOS)
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_projeto.settings')
django.setup()

from barbearia_app.models import Barbeiro, Servico

# --- 1. BARBEIROS (Mantivemos iguais) ---
BARBEIROS_PARA_CADASTRAR = [
    {"nome_completo": "Maria Oliveira", "especialidade": "Coloração e Cortes Modernos"},
    {"nome_completo": "João Silva", "especialidade": "Barba e Tradicional"},
    {"nome_completo": "Guilherme Amaral", "especialidade": "Cortes Infantis"},
    {"nome_completo": "Gustavo Mercante", "especialidade": "Visagismo e Design de Barba"},
]

# --- 2. SERVIÇOS (AJUSTADOS PARA MÚLTIPLOS DE 30 MIN) ---
SERVICOS_PARA_CADASTRAR = [
    # Corte: Arredondado para 1 hora (era 45 min) para serviço premium
    {"nome_servico": "Corte Masculino", "preco": Decimal("50.00"), "duracao_minutos": 60}, 
    
    # Barba: Arredondado para 30 min (era 40 min) - Ajustar o ritmo para 30
    {"nome_servico": "Barba Completa", "preco": Decimal("45.00"), "duracao_minutos": 30}, 
    
    # Combo: 1h 30min (Perfeito, são 3 blocos de 30)
    {"nome_servico": "Corte + Barba", "preco": Decimal("85.00"), "duracao_minutos": 90}, 
    
    # Pigmentação: 30 min (1 bloco)
    {"nome_servico": "Pigmentação de Barba", "preco": Decimal("60.00"), "duracao_minutos": 30}, 
    
    # Corte Feminino: 1 hora (2 blocos)
    {"nome_servico": "Corte Feminino (Curto/Médio)", "preco": Decimal("70.00"), "duracao_minutos": 60},
]

def populate_barbeiros():
    print("--- Populando Barbeiros ---")
    for b_data in BARBEIROS_PARA_CADASTRAR:
        barbeiro, created = Barbeiro.objects.get_or_create(
            nome_completo=b_data['nome_completo'],
            defaults={'especialidade': b_data.get('especialidade', '')}
        )
        if created:
            print(f"  [+] Criado Barbeiro: {barbeiro.nome_completo}")
        else:
            print(f"  [=] Barbeiro já existe: {barbeiro.nome_completo}")

def populate_servicos():
    print("\n--- Populando Serviços ---")
    for s_data in SERVICOS_PARA_CADASTRAR:
        servico, created = Servico.objects.get_or_create(
            nome_servico=s_data['nome_servico'],
            defaults={
                'preco': s_data['preco'], 
                'duracao_minutos': s_data['duracao_minutos']
            }
        )
        if created:
            print(f"  [+] Criado Serviço: {servico.nome_servico} ({s_data['duracao_minutos']} min)")
        else:
            # ATUALIZA OS VALORES SE JÁ EXISTIR
            servico.preco = s_data['preco']
            servico.duracao_minutos = s_data['duracao_minutos']
            servico.save()
            print(f"  [UP] Serviço atualizado: {servico.nome_servico} -> Agora é {servico.duracao_minutos} min")

if __name__ == '__main__':
    populate_barbeiros()
    populate_servicos()
    print("\nAtualização de tempos concluída com sucesso.")