from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from django.http import HttpResponseRedirect
from django.db.models import Q, ProtectedError, Sum
from django.shortcuts import redirect, get_object_or_404, render
from collections import defaultdict
from django.utils import timezone
from datetime import timedelta, datetime
from django.views.generic import ListView, CreateView, DeleteView, DetailView, UpdateView, TemplateView, View
from .forms import ClienteForm, VeiculoForm, LocacaoForm, EncerrarLocacaoForm, DespesaForm
from .models import Cliente, Veiculo, Locacao, Despesa, Pagamento

class ClieneBaseView:
    model = Cliente
    success_url = reverse_lazy('cliente_list')

class ClienteList(ClieneBaseView, ListView):
    template_name = "clientes/cliente_list.html"
    context_object_name = "clientes"
    ordering = ["-criado_em"]
    paginate_by = 30

    def get_queryset(self):
        queryset = Cliente.objects.all()
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(nome__icontains=q) |
                Q(cpf__icontains=q) |
                Q(cnh_numero__icontains=q)
            ).distinct()
        return queryset

class ClienteCreate(ClieneBaseView, CreateView):
    template_name = "clientes/cliente_adicionar.html"
    form_class = ClienteForm

class ClienteDetail(ClieneBaseView, DetailView):
    template_name = "clientes/cliente_detalhe.html"

class ClienteUptade(ClieneBaseView, UpdateView):
    template_name = "clientes/cliente_editar.html"
    fields = [ "nome", "cpf", "data_nascimento", "telefone", "email", "endereco", "cnh_numero", "cnh_validade",
                "observacao", "documento_com_foto"
    ]
   
class ClienteDelete(ClieneBaseView, DeleteView):
    template_name = "clientes/cliente_excluir.html"

    def post(self, request, *args, **kwargs):
        cliente = self.get_object()
        # 🔹 Verifica se o cliente possui locações vinculadas
        if cliente.locacoes.exists():
            messages.error(request, f"❌ Não é possível excluir {cliente.nome} porque ele possui locações vinculadas.")
            return redirect(self.success_url)
        try:
            cliente.delete()
            messages.success(request, f"✅ Cliente {cliente.nome} excluído com sucesso.")
        except Exception as e:
            messages.error(request, f"❌ Erro ao excluir cliente: {e}")
        return redirect(self.success_url)

#-------------------- VEICULOS ------------------------------------------------------------

class VeiculoBaseView:
    model = Veiculo
    success_url = reverse_lazy('veiculo_list')

class VeiculoList(VeiculoBaseView, ListView):
    template_name = "veiculos/veiculo_list.html"
    context_object_name = 'veiculos'
    paginate_by = 30

    def get_queryset(self):
        queryset = Veiculo.objects.all()
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if q:
            queryset = queryset.filter(
                Q(modelo__icontains=q) |
                Q(placa__icontains=q) |
                Q(marca__icontains=q) 
            ).distinct()
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('-status', '-id')
    

class VeiculoCreate(VeiculoBaseView, CreateView):
    template_name = "veiculos/veiculo_adicionar.html"
    form_class = VeiculoForm

class VeiculoDetail(VeiculoBaseView, DetailView):
    template_name = "veiculos/veiculo_detalhe.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        veiculo = self.object
        total_despesas = (Despesa.objects.filter(veiculo=veiculo).aggregate(total=Sum("valor"))["total"] or 0)
        context["total_despesas"] = total_despesas
       
        return context

class VeiculoUpdate(VeiculoBaseView, UpdateView):
    template_name = "veiculos/veiculo_editar.html"
    form_class = VeiculoForm

class VeiculoDelete(VeiculoBaseView, DeleteView):
    template_name = "veiculos/veiculo_excluir.html"

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        try:
            self.object.delete()
            messages.success(request, "Veículo excluído com sucesso.")
        except ProtectedError:
            messages.error(request, "Este veículo não pode ser excluído pois está vinculado a uma locação ativa.")
        return redirect(self.success_url)

#-------------------- LOCAÇÃO ------------------------------------------------------------

class LocacaoBaseView:
    model = Locacao
    form_class = LocacaoForm
    success_url = reverse_lazy('locacao_list')

class LocacaoList(LocacaoBaseView, ListView):
    template_name = "locacao/locacao_list.html"
    context_object_name = "locacoes"
    ordering = ["status"]
    paginate_by = 30

    def get_queryset(self):
        queryset = Locacao.objects.all()
        q = self.request.GET.get("q")
        status = self.request.GET.get("status")
        if q:
            queryset = queryset.filter(
                Q(cliente__nome__icontains = q) |
                Q(veiculo__placa__icontains=q) |
                Q(veiculo__modelo__icontains = q) 
            ).distinct()
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by('status')

class LocacaoDetail(LocacaoBaseView, DetailView):
    template_name = "locacao/locacao_detalhe.html"

class LocacaoCreate(LocacaoBaseView, CreateView):
    template_name = "locacao/locacao_adicionar.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['veiculos_disponiveis'] = Veiculo.objects.filter(status="disponível")
        context['clientes'] = Cliente.objects.all()
        return context
    
class LocacaoUpdate(UpdateView):
    model = Locacao
    form_class = LocacaoForm
    template_name = "locacao/locacao_editar.html"
    success_url = reverse_lazy('locacao_list')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        #  Bloqueia edição se estiver encerrada
        if self.object.status == "encerrada":
            messages.error(request, "Não é possível editar uma locação encerrada.")
            return HttpResponseRedirect(reverse('locacao_list'))
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clientes'] = Cliente.objects.all()
        # Inclui o veículo atual mesmo que não esteja disponível
        if self.object.veiculo:
            context['veiculos_disponiveis'] = Veiculo.objects.filter(status="disponível") | Veiculo.objects.filter(id=self.object.veiculo.id)
        else:
            context['veiculos_disponiveis'] = Veiculo.objects.filter(status="disponível")
        return context
    

class LocacaoDelete(LocacaoBaseView, DeleteView):
    template_name = "locacao/locacao_excluir.html"
    success_url = reverse_lazy('locacao_list')

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        #  Verifica se a locação está encerrada
        if obj.status != "encerrada":
            messages.error(request, "❌ Somente Locações encerradas é possível excluir.")
            return redirect(self.success_url)
        try:
            obj.delete()
            messages.success(request, f"✅ Locação {obj} excluída com sucesso.")
        except Exception as e:
            messages.error(request, f"❌ Erro ao excluir locação: {e}")
        return redirect(self.success_url)

class EncerrarLocacaoView(UpdateView):
    model = Locacao
    form_class = EncerrarLocacaoForm
    template_name = "locacao/locacao_encerrar.html"
    context_object_name = "locacao"

    def form_valid(self, form):
        locacao = form.save(commit=False)
        km_fim = form.cleaned_data.get("km_fim")
        caucao_status = form.cleaned_data.get("caucao_status")

        #  Validação do KM
        if km_fim <= locacao.km_inicio:
            form.add_error("km_fim", "O Km final deve ser maior que o Km inicial.")
            return self.form_invalid(form)

        #  Atualiza informações da locação
        locacao.km_fim = km_fim
        locacao.status = "encerrada"
        locacao.fim = timezone.now()
        locacao.caucao_status = caucao_status  # devolvido ou retido
        locacao.save()

        #  Atualiza o veículo
        veiculo = locacao.veiculo
        veiculo.status = "disponível"
        veiculo.km_atual = km_fim
        veiculo.save()

        #  Mensagem de feedback
        if locacao.caucao_status == "devolvido":
            msg_caucao = "Caução devolvido ao cliente."
        elif locacao.caucao_status == "retido":
            msg_caucao = "Caução retido devido a pendências."
        else:
            msg_caucao = "Caução permanece pendente."

        messages.success(self.request, f"Locação encerrada com sucesso. {msg_caucao}")

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("locacao_detalhe", args=[self.object.pk])
    

#-------------------------------- RECEBER PAGAMENOTS -------------------------------------

class ReceberListView(TemplateView):
    template_name = "financeiro/receber.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.now().date()
        locacoes = Locacao.objects.filter(status="andamento")
        q = self.request.GET.get("q")

        if q:
            locacoes = locacoes.filter(
                Q(cliente__nome__icontains=q) |
                Q(veiculo__modelo__icontains=q)
            )
            context["q"] = q

        dias_semana = {
            0: "Segunda-feira",
            1: "Terça-feira",
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo",
        }

        agrupado = defaultdict(list)
        totais_por_dia = defaultdict(float)

        for loc in locacoes:
            dia_semana = loc.inicio.weekday()
            parcela = loc.valor_total_locacao / loc.quantidade_semanas

            semanas_pagas = loc.semanas_pagas
            semanas_restantes = loc.quantidade_semanas - semanas_pagas
            total_pago = semanas_pagas * parcela
            saldo = loc.valor_total_locacao - total_pago

            proximo_pagamento = loc.inicio.date() + timedelta(days=(semanas_pagas + 1) * 7)

            #  Último pagamento real do banco
            ultimo_pagamento_obj = loc.pagamentos.order_by("-data").first()
            ultimo_pagamento = ultimo_pagamento_obj.data if ultimo_pagamento_obj else None

            #  Status visual
            if proximo_pagamento <= hoje:
                status = "vencido"
            elif proximo_pagamento <= hoje + timedelta(days=3):
                status = "proximo"
            else:
                status = "ok"

            totais_por_dia[dias_semana[dia_semana]] += float(saldo)

            agrupado[dias_semana[dia_semana]].append({
                "locacao": loc,
                "cliente": loc.cliente.nome,
                "veiculo": loc.veiculo.modelo,
                "valor_total": loc.valor_total_locacao,
                "parcela": parcela,
                "semanas_pagas": semanas_pagas,
                "semanas_restantes": semanas_restantes,
                "total_pago": total_pago,
                "saldo": saldo,
                "proximo_pagamento": proximo_pagamento,
                "ultimo_pagamento": ultimo_pagamento, 
                "status": status,
            })

        context["totais_por_dia"] = dict(totais_por_dia)
        context["agrupado"] = dict(agrupado)
        return context

class EfetuarPagamentoView(View):
    template_name = "financeiro/receber_pagamento.html"

    def get(self, request, pk):
        locacao = get_object_or_404(Locacao, pk=pk)
        parcela = locacao.valor_total_locacao / locacao.quantidade_semanas
        semanas_restantes = locacao.quantidade_semanas - locacao.semanas_pagas

        contexto = {
            "locacao": locacao,
            "parcela": parcela,
            "semanas_pagas": locacao.semanas_pagas,
            "semanas_restantes": semanas_restantes,
        }
        return render(request, self.template_name, contexto)

    def post(self, request, pk):
        locacao = get_object_or_404(Locacao, pk=pk)
        parcela = locacao.valor_total_locacao / locacao.quantidade_semanas

        # Evita pagamento além do limite
        if locacao.semanas_pagas >= locacao.quantidade_semanas:
            messages.warning(request, "✅ Todas as parcelas já foram quitadas.")
            return redirect("receber")

        #  1 — Registra pagamento no banco
        Pagamento.objects.create(
            locacao=locacao,
            valor=parcela
            # data é salva automaticamente pelo auto_now_add=True
        )

        #  2 — Atualiza semanas pagas da locação
        locacao.semanas_pagas += 1
        locacao.save()

        messages.success(
            request,
            f"💰 Pagamento da semana {locacao.semanas_pagas}/{locacao.quantidade_semanas} registrado!"
        )

        return redirect("receber")
    

class DashboardView(TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoje = timezone.now().date()

        # ------------------------------------------------------------
        #  FILTRO DE DATA
        # ------------------------------------------------------------
        data_inicio = self.request.GET.get("data_inicio")
        data_fim = self.request.GET.get("data_fim")

        if not data_inicio or not data_fim:
            primeiro_dia = hoje.replace(day=1)
            if hoje.month == 12:
                proximo_mes = hoje.replace(year=hoje.year + 1, month=1, day=1)
            else:
                proximo_mes = hoje.replace(month=hoje.month + 1, day=1)
            ultimo_dia = proximo_mes - timedelta(days=1)
            data_inicio, data_fim = primeiro_dia, ultimo_dia
        else:
            data_inicio = timezone.datetime.strptime(data_inicio, "%Y-%m-%d").date()
            data_fim = timezone.datetime.strptime(data_fim, "%Y-%m-%d").date()

        # ------------------------------------------------------------
        #  LOCAÇÕES
        # ------------------------------------------------------------
        locacoes_qs = Locacao.objects.select_related("cliente", "veiculo").filter(
            inicio__lte=data_fim
        ).filter(
            fim__gte=data_inicio
        ) | Locacao.objects.filter(status="andamento")

        locacoes_qs = locacoes_qs.distinct()

        locacoes = []
        for loc in locacoes_qs:
            inicio_date = loc.inicio.date() if hasattr(loc.inicio, "date") else loc.inicio
            duracao_dias = (loc.quantidade_semanas or 0) * 7
            fim_estimado = inicio_date + timedelta(days=max(duracao_dias - 1, 0))

            fim_real = getattr(loc, "fim", None)
            if fim_real:
                fim_date = fim_real.date() if hasattr(fim_real, "date") else fim_real
            else:
                fim_date = fim_estimado

            if fim_date >= data_inicio and inicio_date <= data_fim:
                locacoes.append(loc)

        # ------------------------------------------------------------
        #  DESPESAS
        # ------------------------------------------------------------
        despesas = Despesa.objects.filter(data__range=[data_inicio, data_fim])

        # ------------------------------------------------------------
        #  RESUMO FINANCEIRO
        # ------------------------------------------------------------
        total_receber = 0
        total_pago = 0
        total_saldo = 0

        for loc in locacoes:
            parcela = loc.valor_total_locacao / loc.quantidade_semanas if loc.quantidade_semanas > 0 else 0
            # 🔹 Se o caução foi devolvido, não soma ao total_pago
            caucao_valor = loc.caucao if getattr(loc, "caucao_status", "retido") == "retido" else 0

            pago = loc.semanas_pagas * parcela + caucao_valor
            saldo = loc.valor_total_locacao - pago

            total_receber += loc.valor_total_locacao
            total_pago += pago
            total_saldo += saldo

        total_despesas = despesas.aggregate(total=Sum("valor"))["total"] or 0
        lucro_liquido = total_pago - total_despesas

        resumo = {
            "total_receber": total_receber,
            "total_pago": total_pago,
            "saldo_a_receber": total_saldo,
            "total_despesas": total_despesas,
            "lucro_liquido": lucro_liquido,
        }

        # ------------------------------------------------------------
        #  OUTROS DADOS
        # ------------------------------------------------------------
        total_veiculos = Veiculo.objects.count()
        veiculos_alugados = Veiculo.objects.filter(status="alugado").count()
        locacoes_ativas = len(locacoes)
        total_clientes = Cliente.objects.count()

        # ------------------------------------------------------------
        #  PAGAMENTOS AGRUPADOS
        # ------------------------------------------------------------
        dias_semana = {
            0: "Segunda-feira",
            1: "Terça-feira",
            2: "Quarta-feira",
            3: "Quinta-feira",
            4: "Sexta-feira",
            5: "Sábado",
            6: "Domingo",
        }

        pagamentos_por_dia = defaultdict(list)

        for loc in locacoes:
            dia_semana = loc.inicio.weekday()
            parcela = loc.valor_total_locacao / loc.quantidade_semanas if loc.quantidade_semanas > 0 else 0
            proximo_pagamento = (
                (loc.inicio.date() if hasattr(loc.inicio, "date") else loc.inicio)
                + timedelta(days=(loc.semanas_pagas + 1) * 7)
            )

            caucao_valor = loc.caucao if getattr(loc, "caucao_status", "retido") == "retido" else 0

            if proximo_pagamento <= hoje:
                status = "vencido"
            elif proximo_pagamento <= hoje + timedelta(days=3):
                status = "proximo"
            else:
                status = "ok"

            pagamentos_por_dia[dias_semana[dia_semana]].append({
                "locacao": loc,
                "cliente": loc.cliente.nome,
                "veiculo": loc.veiculo.modelo,
                "proximo_pagamento": proximo_pagamento,
                "status": status,
                "parcela": parcela,
                "semanas_pagas": loc.semanas_pagas,
                "semanas_restantes": loc.quantidade_semanas - loc.semanas_pagas,
                "valor_recebido": (loc.semanas_pagas * parcela) + caucao_valor,
            })

        # ------------------------------------------------------------
        #  GRÁFICO
        # ------------------------------------------------------------
        labels_chart = list(pagamentos_por_dia.keys())
        data_chart = [len(pagamentos_por_dia[dia]) for dia in labels_chart]

        # ------------------------------------------------------------
        #  CONTEXTO FINAL
        # ------------------------------------------------------------
        context.update({
            "resumo": resumo,
            "pagamentos_por_dia": dict(pagamentos_por_dia),
            "labels_chart": labels_chart,
            "data_chart": data_chart,
            "total_veiculos": total_veiculos,
            "veiculos_alugados": veiculos_alugados,
            "locacoes_ativas": locacoes_ativas,
            "total_clientes": total_clientes,
            "data_inicio": data_inicio,
            "data_fim": data_fim,
        })

        return context


    
#----------------------------- DESPESAS DESPESAS DESPESAS DESPESAS---------------------------------------------

class DespesaBaseView():
    model = Despesa
    form_class = DespesaForm
    success_url = reverse_lazy('despesa_list')

class DespesaListView(ListView):
    model = Despesa
    template_name = "despesa/despesa_list.html"
    context_object_name = "despesas"

    def get_queryset(self):
        qs = super().get_queryset().select_related("veiculo")

        veiculo = self.request.GET.get("veiculo")
        categoria = self.request.GET.get("categoria")
        mes = self.request.GET.get("mes")
        ano = self.request.GET.get("ano")

        if veiculo:
            qs = qs.filter(veiculo_id=veiculo)
        if categoria:
            qs = qs.filter(categoria=categoria)
        if mes:
            qs = qs.filter(data__month=mes)
        if ano:
            qs = qs.filter(data__year=ano)

        return qs.order_by("-data", "-id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["veiculos"] = Veiculo.objects.all()

        #  Total de despesas do filtro atual
        context["total_despesas"] = self.get_queryset().aggregate(total=Sum("valor"))["total"] or 0

        #  Lista de anos com base no campo `data`
        anos = (
            Despesa.objects
            .dates("data", "year", order="DESC")
            .distinct()
        )
        anos = [d.year for d in anos] if anos else [datetime.now().year]

        context["anos"] = anos
        context["meses"] = range(1, 13)
        return context

class DespesaCreateView(DespesaBaseView, CreateView):
    template_name = "despesa/despesa_adicionar.html"
    
class DespesaUpdateView(UpdateView):
    model = Despesa
    form_class = DespesaForm
    template_name = "despesa/despesa_editar.html"
    success_url = reverse_lazy('despesa_list')

    def get_queryset(self):
        return super().get_queryset().select_related("veiculo")
    
class DespesaDeleteView(DeleteView):
    model = Despesa
    template_name = "despesa/despesa_excluir.html"
    success_url = reverse_lazy('despesa_list')