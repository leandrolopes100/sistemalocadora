from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from locar.views import ( ClienteList, ClienteCreate, ClienteDelete, ClienteDetail, ClienteUptade,
                          VeiculoCreate ,VeiculoList, VeiculoDetail, VeiculoUpdate, VeiculoDelete,
                          LocacaoList, LocacaoCreate, LocacaoDetail, LocacaoUpdate, LocacaoDelete,
                          EncerrarLocacaoView, ReceberListView, EfetuarPagamentoView, DashboardView, 
                          DespesaListView, DespesaCreateView, DespesaUpdateView, DespesaDeleteView
                         )

urlpatterns = [
    path("", lambda request: redirect("dashboard/")),
    path('admin/', admin.site.urls),
    path('clientes/', ClienteList.as_view(), name='cliente_list'),
    path('clientes/adicionar/', ClienteCreate.as_view(), name='cliente_adicionar'),
    path('clientes/<int:pk>/excluir/', ClienteDelete.as_view(), name='cliente_excluir'),
    path('clientes/<int:pk>/detalhe/', ClienteDetail.as_view(), name='cliente_detalhe'),
    path('clientes/<int:pk>/editar/', ClienteUptade.as_view(), name ='cliente_editar'),

    path('veiculos/', VeiculoList.as_view(), name='veiculo_list'),
    path('veiculos/adicionar/', VeiculoCreate.as_view(), name='veiculo_adicionar'),
    path('veiculos/<int:pk>/detalhe/', VeiculoDetail.as_view(), name='veiculo_detalhe' ),
    path('veiculos/<int:pk>/editar/', VeiculoUpdate.as_view(), name='veiculo_editar'),
    path('veiculos/<int:pk>/excluir/', VeiculoDelete.as_view(), name="veiculo_excluir"),

    path('locacao/', LocacaoList.as_view(), name='locacao_list'),
    path('locacao/adicionar/', LocacaoCreate.as_view(), name='locacao_adicionar'),
    path('locacao/<int:pk>/detalhe', LocacaoDetail.as_view(), name='locacao_detalhe'),
    path("locacoes/<int:pk>/encerrar/", EncerrarLocacaoView.as_view(), name="locacao_encerrar"),
    path('locacao/<int:pk>/editar/', LocacaoUpdate.as_view(), name="locacao_editar"),
    path('locacao/<int:pk>/excluir/', LocacaoDelete.as_view(), name="locacao_excluir"),

    path("financeiro/receber/", ReceberListView.as_view(), name="receber"),
    path("financeiro/<int:pk>/pagamento/", EfetuarPagamentoView.as_view(), name="pagamento"),

    path("despesa/", DespesaListView.as_view(), name="despesa_list" ),
    path("despesa/adicionar/", DespesaCreateView.as_view(), name='despesa_adicionar'),
    path("despesa/<int:pk>/editar/", DespesaUpdateView.as_view(), name="despesa_editar"),
    path("desepesa/<int:pk>/excluir/", DespesaDeleteView.as_view(), name="despesa_excluir"),


    path('dashboard/', DashboardView.as_view(), name="dashboard")


]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
