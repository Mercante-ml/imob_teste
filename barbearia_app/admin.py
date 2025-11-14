# barbearia_app/admin.py (VERSÃO FINAL CORRIGIDA - SEM DUPLICATAS)

from django.contrib import admin
from .models import Cliente, Barbeiro, Servico, Agendamento, Feriado, BarbeiroIndisponibilidade, ConfiguracaoGeral

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'telefone')
    search_fields = ('nome_completo', 'telefone')

@admin.register(Barbeiro)
class BarbeiroAdmin(admin.ModelAdmin):
    list_display = ('nome_completo', 'telefone', 'especialidade')

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ('nome_servico', 'preco', 'duracao_minutos')
    list_filter = ('duracao_minutos',)

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ('data_agendada', 'hora_inicio', 'cliente', 'servico', 'valor_historico', 'status')
    list_filter = ('status', 'data_agendada', 'barbeiro')
    search_fields = ('cliente__nome_completo',)
    date_hierarchy = 'data_agendada'
    
    readonly_fields = ('valor_historico',) 

@admin.register(Feriado)
class FeriadoAdmin(admin.ModelAdmin):
    list_display = ('data_feriado', 'nome_feriado', 'abrangencia')

@admin.register(BarbeiroIndisponibilidade)
class BarbeiroIndisponibilidadeAdmin(admin.ModelAdmin):
    list_display = ('barbeiro', 'data_inicio', 'data_fim')

@admin.register(ConfiguracaoGeral)
class ConfiguracaoGeralAdmin(admin.ModelAdmin):
    fieldsets = (
        # SEÇÃO 1: Identidade e Regras Gerais (Unificada)
        ('Identidade e Regras', {
            'fields': ('nome_exibicao', 'logo', 'mensagem_compartilhamento', 'intervalo_agendamento')
        }),
        # SEÇÃO 2: Localização
        ('Localização', {
            'fields': ('endereco_loja', 'link_maps')
        }),
        # SEÇÃO 3: Horários
        ('Horário: Segunda a Sexta', {
            'fields': (('hora_abertura', 'hora_fechamento'), ('hora_inicio_almoco', 'hora_fim_almoco'))
        }),
        ('Horário: Sábado', {
            'fields': ('abre_sabado', ('hora_abertura_sabado', 'hora_fechamento_sabado'))
        }),
        ('Horário: Domingo', {
            'fields': ('abre_domingo', ('hora_abertura_domingo', 'hora_fechamento_domingo'))
        }),
        ('Horário: Feriados', {
            'fields': ('trabalha_feriados', ('hora_abertura_feriado', 'hora_fechamento_feriado'))
        }),
    )
    def has_add_permission(self, request): return not ConfiguracaoGeral.objects.exists()