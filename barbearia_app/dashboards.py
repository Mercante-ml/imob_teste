# barbearia_app/dashboards.py

import plotly.graph_objects as go
from django_plotly_dash import DjangoDash
from barbearia_app.models import Agendamento
from django.db.models import F
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import copy

# --- Theme Colors (Centralized) ---
cores_tema = {
    'azul_principal': '#3498DB', 'verde': '#2ecc71', 'amarelo': '#f1c40f',
    'vermelho': '#e74c3c', 'cinza_azulado': '#2c3e50', 'texto': '#FFFFFF',
    'fundo_card': 'rgba(0,0,0,0)', 'fundo_plot': 'rgba(0,0,0,0)'
}

# --- Standard Transparent Layout ---
layout_transparente = go.Layout(
    paper_bgcolor=cores_tema['fundo_card'],
    plot_bgcolor=cores_tema['fundo_plot'],
    font_color=cores_tema['texto'],
    showlegend=True,
    margin=dict(l=20, r=20, t=60, b=20)
)
layout_legenda_topo = copy.deepcopy(layout_transparente)
layout_legenda_topo.update(legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))

# ===============================================
# MAIN UNIFIED APPLICATION
# ===============================================
app = DjangoDash('VisaoGeralDashboard')

# --- Data Retrieval Functions ---
def get_dados_agendamentos():
    qs = Agendamento.objects.all().select_related('servico', 'barbeiro')
    df = pd.DataFrame.from_records(
        qs.values(
            'id', 'status', 'valor_historico',
            'data_agendada',
            servico_nome=F('servico__nome_servico'),
            barbeiro_nome=F('barbeiro__nome_completo')
        )
    )
    if not df.empty:
        df['data_agendada'] = pd.to_datetime(df['data_agendada'])
        df['dia_semana'] = df['data_agendada'].dt.dayofweek
        df['dia_mes'] = df['data_agendada'].dt.day
    return df

# --- Filter Options ---
def get_opcoes_mes_ano():
    try:
        df = get_dados_agendamentos()
        if df.empty: return [{'label': 'Sem Dados', 'value': 'all'}]

        df['ano_mes_str'] = df['data_agendada'].dt.strftime('%Y-%m')
        meses_map = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                     7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
        df['mes_label'] = df['data_agendada'].dt.month.map(meses_map)
        df['ano_label'] = df['data_agendada'].dt.year.astype(str)
        df['ano_mes_label'] = df['mes_label'] + '/' + df['ano_label']

        opcoes = df[['ano_mes_str', 'ano_mes_label']].drop_duplicates().sort_values(by='ano_mes_str', ascending=False)
        lista_opcoes = [{'label': row['ano_mes_label'], 'value': row['ano_mes_str']} for _, row in opcoes.iterrows()]
        return [{'label': 'Todo o Período', 'value': 'all'}] + lista_opcoes
    except Exception: # Fallback in case DB is not ready
        return [{'label': 'Carregando...', 'value': 'all'}]


opcoes_status = [
    {'label': 'Todos os Status', 'value': 'all'},
    {'label': 'Pendente', 'value': 'pendente'},
    {'label': 'Confirmado', 'value': 'confirmado'},
    {'label': 'Realizado', 'value': 'realizado'},
    {'label': 'Cancelado', 'value': 'cancelado'},
]

# --- Main Layout as a function to defer DB query ---
def create_layout():
    return html.Div(
        style={'backgroundColor': '#1E293B', 'padding': '20px'},
        children=[
            # -- Filters Row --
            html.Div(className='row', children=[
                html.Div(className='col-md-6', children=[
                    dcc.Dropdown(
                        id='filtro-mes-ano',
                        options=get_opcoes_mes_ano(),
                        value='all',
                        clearable=False,
                        style={'color': '#333'}
                    )
                ]),
                html.Div(className='col-md-6', children=[
                    dcc.Dropdown(
                        id='filtro-status',
                        options=opcoes_status,
                        value='all',
                        clearable=False,
                        style={'color': '#333'}
                    )
                ]),
            ]),

            # -- KPIs and Donut Chart Row --
            html.Div(className='row mt-4', children=[
                html.Div(className='col-md-8', children=[
                    dcc.Graph(id='kpi-graph', figure=go.Figure().update_layout(layout_transparente), config={'displayModeBar': False})
                ]),
                html.Div(className='col-md-4', children=[
                    dcc.Graph(id='donut-status-graph', figure=go.Figure().update_layout(layout_legenda_topo, title_text="Carregando..."), config={'displayModeBar': False})
                ]),
            ]),

            # -- Bar Charts Row --
            html.Div(className='row mt-4', children=[
                html.Div(className='col-md-6', children=[
                     dcc.Graph(id='servico-bar-graph', figure=go.Figure().update_layout(layout_transparente), config={'displayModeBar': False})
                ]),
                html.Div(className='col-md-6', children=[
                     dcc.Graph(id='barbeiro-graph', figure=go.Figure().update_layout(layout_legenda_topo), config={'displayModeBar': False})
                ]),
            ]),

            # -- Time Series and Weekday Row --
            html.Div(className='row mt-4', children=[
                html.Div(className='col-md-8', children=[
                    dcc.Graph(id='agend-dia-graph', figure=go.Figure().update_layout(layout_legenda_topo, title_text="Selecione um Mês/Ano"), config={'displayModeBar': False})
                ]),
                html.Div(className='col-md-4', children=[
                     dcc.Graph(id='dia-semana-graph', figure=go.Figure().update_layout(layout_transparente), config={'displayModeBar': False})
                ]),
            ]),
        ]
    )

app.layout = create_layout

# ===============================================
# GENERAL FILTERING FUNCTION
# ===============================================
def filtrar_df(filtro_mes, filtro_status):
    df = get_dados_agendamentos()
    if df.empty: return df
    if filtro_mes and filtro_mes != 'all':
        df = df[df['data_agendada'].dt.strftime('%Y-%m') == filtro_mes]
    if filtro_status and filtro_status != 'all':
        df = df[df['status'] == filtro_status]
    return df

# ===============================================
# CALLBACKS (All associated with the single app)
# ===============================================

# --- Donut Chart Callback ---
@app.callback(
    Output('donut-status-graph', 'figure'),
    [Input('filtro-mes-ano', 'value'), Input('filtro-status', 'value')]
)
def update_donut(filtro_mes, filtro_status):
    df = filtrar_df(filtro_mes, filtro_status)
    if df.empty: return go.Figure().update_layout(layout_legenda_topo, title_text="Sem dados")

    dados = df.groupby('status').size().reset_index(name='total')
    labels_map = {'confirmado': 'Confirmado', 'realizado': 'Realizado', 'cancelado': 'Cancelado', 'pendente': 'Pendente'}
    color_map = {'Confirmado': cores_tema['verde'], 'Realizado': cores_tema['azul_principal'], 'Cancelado': cores_tema['vermelho'], 'Pendente': cores_tema['amarelo']}
    labels = dados['status'].map(labels_map)
    values = dados['total']
    cores_grafico = labels.map(color_map)
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=.5, marker=dict(colors=cores_grafico, line=dict(color='#2c3e50', width=2))))
    fig.update_layout(layout_legenda_topo, title_text="Status dos Agendamentos")
    return fig

# --- KPIs Callback ---
@app.callback(
    Output('kpi-graph', 'figure'),
    [Input('filtro-mes-ano', 'value'), Input('filtro-status', 'value')]
)
def update_kpis(filtro_mes, filtro_status):
    df_global = get_dados_agendamentos()
    if df_global.empty: return go.Figure().update_layout(layout_transparente, title_text="Sem dados")

    df = df_global.copy()
    if filtro_mes and filtro_mes != 'all':
        df = df[df['data_agendada'].dt.strftime('%Y-%m') == filtro_mes]

    total_agend = len(df)

    if filtro_status and filtro_status != 'all':
        df_kpi = df[df['status'] == filtro_status]
    else:
        df_kpi = df.copy()

    realizados_df = df_kpi[df_kpi['status'] == 'realizado']
    faturamento_total = realizados_df['valor_historico'].sum()
    contagem_realizados = realizados_df.shape[0]
    ticket_medio = (faturamento_total / contagem_realizados) if contagem_realizados > 0 else 0

    taxa_no_show_base = len(df)
    taxa_no_show_cancelados = df[df['status'] == 'cancelado'].shape[0]
    taxa_no_show = (taxa_no_show_cancelados / taxa_no_show_base) if taxa_no_show_base > 0 else 0

    fig = go.Figure()
    fig.add_trace(go.Indicator(mode="number", value=total_agend, title={"text": "Total Agendamentos"}, domain={'row': 0, 'column': 0}))
    fig.add_trace(go.Indicator(mode="number", value=ticket_medio, title={"text": "Ticket Médio (R$)"}, number={'prefix': "R$", 'valueformat': '.2f'}, domain={'row': 0, 'column': 1}))
    fig.add_trace(go.Indicator(mode="number", value=faturamento_total, title={"text": "Faturamento (R$)"}, number={'prefix': "R$", 'valueformat': '.2f'}, domain={'row': 1, 'column': 0}))
    fig.add_trace(go.Indicator(mode="number", value=taxa_no_show, title={"text": "Taxa de No-Show"}, number={'suffix': "%", 'valueformat': '.1%'}, domain={'row': 1, 'column': 1}))
    fig.update_layout(grid={'rows': 2, 'columns': 2, 'pattern': "independent"}, paper_bgcolor='rgba(0,0,0,0)', font_color=cores_tema['texto'], title_text="Métricas Principais")
    return fig

# --- Service Type Bar Chart Callback ---
@app.callback(
    Output('servico-bar-graph', 'figure'),
    [Input('filtro-mes-ano', 'value'), Input('filtro-status', 'value')]
)
def update_servicos(filtro_mes, filtro_status):
    df = filtrar_df(filtro_mes, filtro_status)
    if df.empty: return go.Figure().update_layout(layout_transparente, title_text="Sem dados")
    dados = df.groupby('servico_nome').size().reset_index(name='total').sort_values(by='total', ascending=False)
    fig = go.Figure(go.Bar(x=dados['servico_nome'], y=dados['total'], marker_color=cores_tema['azul_principal']))
    fig.update_layout(layout_transparente, title_text="Agendamentos por Tipo de Serviço")
    return fig

# --- Barber by Status Bar Chart Callback ---
@app.callback(
    Output('barbeiro-graph', 'figure'),
    [Input('filtro-mes-ano', 'value'), Input('filtro-status', 'value')]
)
def update_barbeiro(filtro_mes, filtro_status):
    df = filtrar_df(filtro_mes, filtro_status)
    if df.empty: return go.Figure().update_layout(layout_legenda_topo, title_text="Sem dados")
    dados = df.groupby(['barbeiro_nome', 'status']).size().reset_index(name='total')
    fig = go.Figure()
    status_unicos = dados['status'].unique()
    labels_map = {'confirmado': 'Confirmado', 'realizado': 'Realizado', 'cancelado': 'Cancelado', 'pendente': 'Pendente'}
    color_map = {'Confirmado': cores_tema['verde'], 'Realizado': cores_tema['azul_principal'], 'Cancelado': cores_tema['vermelho'], 'Pendente': cores_tema['amarelo']}
    for status in status_unicos:
        df_status = dados[dados['status'] == status]
        fig.add_trace(go.Bar(
            x=df_status['barbeiro_nome'], y=df_status['total'],
            name=labels_map.get(status), marker_color=color_map.get(labels_map.get(status))
        ))
    fig.update_layout(layout_legenda_topo, barmode='stack', title_text="Agendamentos por Barbeiro")
    return fig

# --- Appointments by Day Bar Chart Callback ---
@app.callback(
    Output('agend-dia-graph', 'figure'),
    [Input('filtro-mes-ano', 'value'), Input('filtro-status', 'value')]
)
def update_agend_dia(filtro_mes, filtro_status):
    df = filtrar_df(filtro_mes, filtro_status)
    if (filtro_mes == 'all') or df.empty:
        return go.Figure().update_layout(layout_legenda_topo, title_text="Selecione um Mês/Ano para ver os detalhes diários")
    dados = df.groupby(['dia_mes', 'status']).size().reset_index(name='total')
    fig = go.Figure()
    status_unicos = dados['status'].unique()
    labels_map = {'confirmado': 'Confirmado', 'realizado': 'Realizado', 'cancelado': 'Cancelado', 'pendente': 'Pendente'}
    color_map = {'Confirmado': cores_tema['verde'], 'Realizado': cores_tema['azul_principal'], 'Cancelado': cores_tema['vermelho'], 'Pendente': cores_tema['amarelo']}
    for status in status_unicos:
        df_status = dados[dados['status'] == status]
        fig.add_trace(go.Bar(
            x=df_status['dia_mes'], y=df_status['total'],
            name=labels_map.get(status), marker_color=color_map.get(labels_map.get(status))
        ))
    fig.update_layout(layout_legenda_topo, barmode='stack', xaxis_title="Dia do Mês", title_text="Volume de Agendamentos por Dia do Mês")
    return fig

# --- Day of the Week Bar Chart Callback ---
@app.callback(
    Output('dia-semana-graph', 'figure'),
    [Input('filtro-mes-ano', 'value'), Input('filtro-status', 'value')]
)
def update_dia_semana(filtro_mes, filtro_status):
    df = filtrar_df(filtro_mes, filtro_status)
    if df.empty: return go.Figure().update_layout(layout_transparente, title_text="Sem dados")
    dados = df.groupby('dia_semana').size().reset_index(name='total')
    dias_map = {0: 'Seg', 1: 'Ter', 2: 'Qua', 3: 'Qui', 4: 'Sex', 5: 'Sáb', 6: 'Dom'}
    dados['dia_nome'] = dados['dia_semana'].map(dias_map)
    dados = dados.set_index('dia_semana').reindex(range(7)).reset_index().fillna(0) # Ensures all days are present
    fig = go.Figure(go.Bar(x=dados['dia_nome'], y=dados['total'], marker_color=cores_tema['azul_principal']))
    fig.update_layout(layout_transparente, xaxis_title="Dia da Semana", title_text="Agendamentos por Dia da Semana")
    return fig
