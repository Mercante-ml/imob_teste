# barbearia_app/models.py (VERSÃO COM TRAVA DE PREÇO HISTÓRICO)

from django.db import models
from datetime import timedelta, date, time, datetime
from django.utils import timezone

# --- CLIENTE ---
class Cliente(models.Model):
    nome_completo = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, unique=True)
    def __str__(self): return self.nome_completo

# --- BARBEIRO ---
class Barbeiro(models.Model):
    nome_completo = models.CharField(max_length=200)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    especialidade = models.CharField(max_length=100, blank=True, null=True)
    def __str__(self): return self.nome_completo

# --- SERVIÇO ---
class Servico(models.Model):
    DURACAO_CHOICES = [
        (30, '30 minutos'), (60, '1 hora'), (90, '1 hora e 30 min'),
        (120, '2 horas'), (150, '2 horas e 30 min'), (180, '3 horas'),
    ]
    nome_servico = models.CharField(max_length=100)
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    duracao_minutos = models.IntegerField(choices=DURACAO_CHOICES, help_text="Duração múltipla de 30 min")

    def __str__(self): return self.nome_servico

# --- AGENDAMENTO (COM CORREÇÃO FINANCEIRA) ---
class Agendamento(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    
    # NOVO CAMPO: Salva o preço no momento da venda
    valor_historico = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        blank=True, 
        null=True, 
        verbose_name="Valor Cobrado (R$)",
        help_text="Valor do serviço no momento do agendamento."
    )

    data_agendada = models.DateField()
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField(blank=True, null=True)
    data_criacao = models.DateTimeField(auto_now_add=True)
    lembrete_diario_enviado = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ('confirmado', 'Confirmado'), ('cancelado', 'Cancelado'),
        ('realizado', 'Realizado'), ('pendente', 'Pendente'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    class Meta: ordering = ['data_agendada', 'hora_inicio']

    def save(self, *args, **kwargs):
        # 1. Calcula Hora Fim
        if self.servico and self.hora_inicio and not self.hora_fim:
            combined = datetime.combine(self.data_agendada, self.hora_inicio)
            self.hora_fim = (combined + timedelta(minutes=self.servico.duracao_minutos)).time()
        
        # 2. Grava o Valor Histórico (Snapshot de Preço)
        # Só grava se estiver vazio (criação), para não sobrescrever se o dono deu um desconto manual depois.
        if self.servico and self.valor_historico is None:
            self.valor_historico = self.servico.preco

        super().save(*args, **kwargs)

    def __str__(self): return f"{self.cliente} - {self.data_agendada}"

# --- FERIADO ---
class Feriado(models.Model):
    data_feriado = models.DateField(unique=True)
    nome_feriado = models.CharField(max_length=100)
    ABRANGENCIA_CHOICES = [('nacional', 'Nacional'), ('estadual_GO', 'Estadual (Goiás)'), ('municipal_Goiania', 'Municipal (Goiânia)')]
    abrangencia = models.CharField(max_length=50, choices=ABRANGENCIA_CHOICES, default='nacional')
    def __str__(self): return f"{self.nome_feriado} ({self.data_feriado})"

# --- INDISPONIBILIDADE ---
class BarbeiroIndisponibilidade(models.Model):
    barbeiro = models.ForeignKey(Barbeiro, on_delete=models.CASCADE, related_name='indisponibilidades')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    motivo = models.CharField(max_length=255, blank=True, null=True)
    class Meta: unique_together = ('barbeiro', 'data_inicio', 'data_fim')
    def save(self, *args, **kwargs):
        if self.data_inicio > self.data_fim: raise ValueError("Fim deve ser depois do início")
        super().save(*args, **kwargs)
    def __str__(self): return f"{self.barbeiro} ({self.data_inicio})"

# --- CONFIGURAÇÃO GERAL ---
class ConfiguracaoGeral(models.Model):
    id_fixo = models.IntegerField(primary_key=True, default=1, editable=False)
    nome_exibicao = models.CharField(max_length=100, default="Barbearia A Tesoura de Ouro")
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    
    mensagem_compartilhamento = models.TextField(
        default="Ei! Conheça nossa Barbearia com esse chatbot super prático para agendamentos. Clique aqui:",
        verbose_name="Mensagem de Compartilhamento",
        help_text="Texto que aparecerá no WhatsApp quando o cliente clicar em compartilhar."
    )
    
    endereco_loja = models.CharField(max_length=255, help_text="Endereço no rodapé", blank=True, null=True)
    link_maps = models.URLField(help_text="Link do Google Maps", blank=True, null=True)
    
    INTERVALO_CHOICES = [(15, '15 min'), (30, '30 min (Padrão)'), (60, '1 hora')]
    intervalo_agendamento = models.IntegerField(default=30, choices=INTERVALO_CHOICES, verbose_name="Grade de Tempo")

    # Horários
    hora_abertura = models.TimeField(default=time(9, 0), verbose_name="Abertura (Seg-Sex)")
    hora_fechamento = models.TimeField(default=time(18, 0), verbose_name="Fechamento (Seg-Sex)")
    hora_inicio_almoco = models.TimeField(default=time(12, 0), verbose_name="Início Almoço (Seg-Sex)")
    hora_fim_almoco = models.TimeField(default=time(13, 0), verbose_name="Fim Almoço (Seg-Sex)")

    abre_sabado = models.BooleanField(default=True, verbose_name="Abre Sábado?")
    hora_abertura_sabado = models.TimeField(default=time(9, 0), verbose_name="Abertura (Sábado)")
    hora_fechamento_sabado = models.TimeField(default=time(14, 0), verbose_name="Fechamento (Sábado)")
    
    abre_domingo = models.BooleanField(default=False, verbose_name="Abre Domingo?")
    hora_abertura_domingo = models.TimeField(default=time(10, 0), blank=True, null=True, verbose_name="Abertura (Domingo)")
    hora_fechamento_domingo = models.TimeField(default=time(14, 0), blank=True, null=True, verbose_name="Fechamento (Domingo)")

    trabalha_feriados = models.BooleanField(default=False, verbose_name="Abre Feriados?")
    hora_abertura_feriado = models.TimeField(default=time(9, 0), blank=True, null=True, verbose_name="Abertura (Feriado)")
    hora_fechamento_feriado = models.TimeField(default=time(16, 0), blank=True, null=True, verbose_name="Fechamento (Feriado)")

    def __str__(self): return f"Configurações ({self.nome_exibicao})"
    class Meta: verbose_name = "Configuração Geral"
    def save(self, *args, **kwargs): self.pk = 1; super().save(*args, **kwargs)