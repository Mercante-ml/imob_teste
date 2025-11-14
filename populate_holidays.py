# populate_holidays.py
import os
import django
from datetime import date
from django.conf import settings

# Configura o ambiente Django para que o script possa acessar os modelos
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'barbearia_projeto.settings')
django.setup()

from barbearia_app.models import Feriado

# Lista de feriados nacionais (datas fixas ou regras simples)
# Datas mais complexas (como Páscoa, Carnaval) exigem cálculo ou biblioteca 'holidays'
FERIADOS_NACIONAIS_FIXOS = {
    (1, 1): "Confraternização Universal",
    (4, 21): "Tiradentes",
    (5, 1): "Dia do Trabalho",
    (9, 7): "Independência do Brasil",
    (10, 12): "Nossa Senhora Aparecida",
    (11, 2): "Finados",
    (11, 15): "Proclamação da República",
    (12, 25): "Natal",
}

# Feriados estaduais de Goiás (Exemplos, verifique a lista oficial)
FERIADOS_ESTADUAIS_GO_FIXOS = {
    # 2025-06-20 é uma sexta-feira - Corpus Christi não é fixo, mas aqui como exemplo
    (6, 20): "Corpus Christi", # Atenção: Corpus Christi é variável! Apenas um exemplo simplificado.
    (7, 26): "Aniversário de Goiás (não é sempre feriado, mas é data importante)"
}

# Feriados municipais de Goiânia (Exemplos, verifique a lista oficial)
FERIADOS_MUNICIPAIS_GOIANIA_FIXOS = {
    (10, 24): "Aniversário de Goiânia",
}

# Função para popular
def populate_feriados(start_year, end_year):
    print(f"Populating holidays from {start_year} to {end_year}...")
    for year in range(start_year, end_year + 1):
        print(f"  Year: {year}")

        # Feriados Nacionais
        for month, day in FERIADOS_NACIONAIS_FIXOS:
            data_feriado = date(year, month, day)
            Feriado.objects.get_or_create(
                data_feriado=data_feriado,
                defaults={'nome_feriado': FERIADOS_NACIONAIS_FIXOS[(month, day)], 'abrangencia': 'nacional'}
            )
            print(f"    Added/Checked National: {data_feriado} - {FERIADOS_NACIONAIS_FIXOS[(month, day)]}")

        # Feriados Estaduais GO
        for month, day in FERIADOS_ESTADUAIS_GO_FIXOS:
            data_feriado = date(year, month, day)
            Feriado.objects.get_or_create(
                data_feriado=data_feriado,
                defaults={'nome_feriado': FERIADOS_ESTADUAIS_GO_FIXOS[(month, day)], 'abrangencia': 'estadual_GO'}
            )
            print(f"    Added/Checked Estadual GO: {data_feriado} - {FERIADOS_ESTADUAIS_GO_FIXOS[(month, day)]}")

        # Feriados Municipais Goiânia
        for month, day in FERIADOS_MUNICIPAIS_GOIANIA_FIXOS:
            data_feriado = date(year, month, day)
            Feriado.objects.get_or_create(
                data_feriado=data_feriado,
                defaults={'nome_feriado': FERIADOS_MUNICIPAIS_GOIANIA_FIXOS[(month, day)], 'abrangencia': 'municipal_Goiania'}
            )
            print(f"    Added/Checked Municipal Goiânia: {data_feriado} - {FERIADOS_MUNICIPAIS_GOIANIA_FIXOS[(month, day)]}")
    
    print("Holiday population complete.")

if __name__ == '__main__':
    # Roda para os próximos 5 anos (de 2025 a 2029)
    populate_feriados(2025, 2035)