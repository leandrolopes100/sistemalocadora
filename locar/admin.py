from django.contrib import admin
from .models import Cliente, Veiculo, Locacao, Despesa, Pagamento

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "cpf", "telefone")
    search_fields = ("nome", "cpf")
    
@admin.register(Veiculo)
class VeiculoAdmin(admin.ModelAdmin):
    list_display = ("marca", "modelo", "placa", "status")
    search_fields = ("placa", "modelo")

@admin.register(Locacao)
class LocacaoAdmin(admin.ModelAdmin):
    list_display = ("veiculo", "cliente", "inicio", "caucao", "valor_semanal")
    search_fields = ("veiculo", "cliente")

@admin.register(Despesa)
class DespesaAdmin(admin.ModelAdmin):
    list_display = ("veiculo", "categoria", "data", "valor")
    search_fields = ("veiculo", "data")

@admin.register(Pagamento)
class PagamentoAdmin(admin.ModelAdmin):
    list_display = ("locacao", "data")
    search_fields = ("locacao", "data")
