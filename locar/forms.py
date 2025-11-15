from django import forms
from .models import Cliente, Veiculo, Locacao, Despesa

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = "__all__"
        widgets = {
            'nome': forms.TextInput(attrs={'placeholder': 'Nome Completo'}),
            'cpf': forms.TextInput(attrs={'placeholder': 'CPF sem pontos'}),
            'data_nascimento': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'telefone': forms.TextInput(attrs={'placeholder': '(00) 00000-0000'}),
            'email': forms.EmailInput(attrs={'placeholder': 'email@exemplo.com'}),
            'endereco': forms.TextInput(attrs={'placeholder': 'Rua, número, bairro, cidade'}),
            'cnh_numero': forms.TextInput(attrs={'placeholder': '0000000000'}),
            'observacao': forms.Textarea(attrs={'placeholder': 'Informações Adicionais'}),
            'cnh_validade': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
        }
    

class VeiculoForm(forms.ModelForm):
    class Meta:
        model = Veiculo
        fields = "__all__"

class LocacaoForm(forms.ModelForm):
    class Meta:
        model = Locacao
        fields = "__all__"
    

class EncerrarLocacaoForm(forms.ModelForm):
    class Meta:
        model = Locacao
        fields = ["km_fim", "caucao_status", "observacoes"]

    km_fim = forms.IntegerField(
        label="Quilometragem final",
        required=True,
        widget=forms.NumberInput(attrs={
            "class": "w-full border rounded px-3 py-2",
            "placeholder": "Informe a quilometragem de devolução"
        })
    )

    caucao_status = forms.ChoiceField(
        label="Situação do Caução",
        choices=Locacao.CAUCAO_STATUS_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            "class": "w-full border rounded px-3 py-2",
        })
    )

    observacoes = forms.CharField(
        label="Observações",
        required=False,
        widget=forms.Textarea(attrs={
            "class": "w-full border rounded px-3 py-2",
            "placeholder": "Informe observações, avarias, multas, etc. (opcional)",
            "rows": 3,
        })
    )

class DespesaForm(forms.ModelForm):
    class Meta:
        model = Despesa
        fields = "__all__"