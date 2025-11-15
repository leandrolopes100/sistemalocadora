from django.db import models
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum
import locale

Usuario = get_user_model()

# Configura locale para moeda (BRL)
try:
    locale.setlocale(locale.LC_ALL, "pt_BR.UTF-8")
except:
    # fallback caso o sistema não tenha o locale BR instalado
    locale.setlocale(locale.LC_ALL, "")

class Cliente(models.Model):
    nome = models.CharField(max_length=100, verbose_name="Nome Completo")
    cpf = models.CharField(max_length=14, unique=True, verbose_name="CPF")
    data_nascimento = models.DateField()
    telefone = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    documento_com_foto = models.FileField(upload_to="documentos-clientes/",blank=True, null=True, verbose_name="Documento com Foto")
    endereco = models.CharField(max_length=300, blank=True)
    cnh_numero = models.CharField(max_length=30, unique=True, blank=True, verbose_name="Registro CNH")
    cnh_validade = models.DateField(blank=True, null=True, verbose_name="Validade CNH")
    observacao = models.TextField(blank=True, null=True, verbose_name="Observação", default="Nenhuma Observação Cadastrada")
    criado_em = models.DateTimeField(auto_now_add=True, editable=False)

    def __str__(self):
        return f"{self.nome}, CPF: ({self.cpf})"
    

# -----------------------------  VEÍCULO -----------------------------------------
class Veiculo(models.Model):
    placa = models.CharField(max_length=7, unique=True)
    marca = models.CharField(max_length=100)
    modelo = models.CharField(max_length=100)
    ano = models.PositiveBigIntegerField()
    chassi = models.CharField(max_length=100, blank=True, null=True)
    km_atual = models.PositiveIntegerField(default=0)
    fipe = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="FIPE")
    renavam = models.CharField(max_length=100, blank=True, null=True, verbose_name="RENAVAM")
    documento_veiculo = models.FileField(upload_to="documentos-veiculos/",blank=True, null=True, verbose_name="CRVL-Digital")
    status = models.CharField(max_length=20, choices=[('disponível', 'Disponível'), ('alugado', 'Alugado') , ('manutencao', 'Manutenção'), ('inativo','Inativo')], null=False, default='disponível')
    foto_veiculo = models.ImageField(upload_to="veiculos/", blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.modelo} - {self.placa}"
    
    
# ----------------------------- LOCAÇÃO VEÍCULO -----------------------------------------
class Locacao(models.Model):
    STATUS_CHOICES = [('andamento', 'Em Andamento'), ('encerrada', 'Encerrada'),]
    FORMA_PAGAMENTO_CHOICES = [("avista", "À Vista"), ("semanal", "Semanal"),]
    CAUCAO_STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("devolvido", "Devolvido"),
        ("retido", "Retido"),
    ]
    veiculo = models.ForeignKey(Veiculo, on_delete=models.PROTECT, related_name='locacoes', null=True, blank=True)
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='locacoes')
    inicio = models.DateTimeField()
    fim = models.DateTimeField()
    km_inicio = models.PositiveIntegerField()
    km_fim = models.PositiveIntegerField(blank=True, null=True)
    valor_semanal = models.DecimalField(max_digits=10, decimal_places=2) 
    quantidade_semanas = models.IntegerField(default=0)
    caucao = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    caucao_status = models.CharField(max_length=20, choices=CAUCAO_STATUS_CHOICES, default="pendente", blank=True, null=True)
    forma_pagamento = models.CharField(max_length=10, choices=FORMA_PAGAMENTO_CHOICES, default="semanal")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='andamento', blank=True, null="True")
    criado_por = models.ForeignKey(Usuario, null=True, blank=True, on_delete=models.SET_NULL)
    criado_em = models.DateTimeField(auto_now_add=True, editable=False)
    documentos_locacao = models.FileField(blank=True, null=True, verbose_name="Documentos")
    observacoes = models.TextField(blank=True)
    semanas_pagas = models.PositiveIntegerField(default=0, editable=False)

    class Meta:
        ordering = ["-criado_em"]

    @property
    def valor_total_locacao(self):
        return self.valor_semanal * self.quantidade_semanas

    def encerrar(self, km_fim): #ATIVA
        self.km_fim = km_fim
        if self.veiculo.status == "alugado":
            self.veiculo.status = "disponível"
            self.veiculo.km_atual = km_fim
            self.veiculo.save()
        self.save()
    
    def delete(self, *args, **kwargs):
        if self.veiculo:  # 🔹 Verifica se existe veículo
            if self.veiculo.status == "alugado":
                self.veiculo.status = "disponível"
                self.veiculo.save()
        super().delete(*args, **kwargs)

    def dias_locacao(self):  #ATIVA
        return (self.fim.date() - self.inicio.date()).days 

    def clean(self):
        if not self.pk and self.veiculo and self.veiculo.status in ["alugado", "inativo", "manutencao"]:
            raise ValidationError(f"O veículo {self.veiculo} não pode ser locado. Verifique o status!")

    def save(self, *args, **kwargs): #ATIVA
        self.full_clean()
        # Se for uma nova locação -> muda o status para "alugado"
        if not self.pk:  
            self.veiculo.status = "alugado"
            self.veiculo.save()
        else:
            # Se já existe e foi informado km_fim -> volta para "disponível"
            if self.km_fim is not None and self.veiculo.status == "alugado":
                self.veiculo.status = "disponível"
                self.veiculo.km_atual = self.km_fim
                self.veiculo.save()

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Locação {self.id} - {self.veiculo} para {self.cliente}"
    

class Pagamento(models.Model): #(RECEBER)
    locacao = models.ForeignKey(Locacao, on_delete=models.CASCADE, related_name="pagamentos")
    data = models.DateTimeField(auto_now_add=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2)

    def clean(self):
        if self.locacao.status != "andamento":
            raise ValidationError("Não é possível registrar pagamento para uma locação encerrada.")

    def save(self, *args, **kwargs):
        self.full_clean()  
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pagamento de R${self.valor} em {self.data.date()} (Locação {self.locacao.id})"
    
    
# ----------------------------- DESPESAS VEÍCULO -----------------------------------------
class Despesa(models.Model):
    veiculo = models.ForeignKey(Veiculo, on_delete=models.CASCADE, related_name='despesas')
    categoria = models.CharField(max_length=50, choices=[('manutencao','Manutenção'), ('multa','Multa'), ('seguro','Seguro'),
            ('ipva','IPVA'),
            ('outros','Outros')
        ]
    )
    descricao = models.CharField(max_length=400)
    data = models.DateField(default=timezone.now)
    valor = models.DecimalField(max_digits=10, decimal_places=2)
    comprovante = models.FileField(upload_to='comprovantes/%Y/%m/%d/', blank=True, null=True)

    def __str__(self):
        return f"{self.categoria} - {self.veiculo} - {self.valor}"