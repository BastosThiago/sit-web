from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from .models import *
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from .forms import *
from unicodedata import normalize
from functools import reduce
from operator import or_
from django.db.models import Q


forms = {
    'categoria': CategoriaForm,
    'curso': CursoForm,
    'inscricao': InscricaoForm,
    'avaliacao': AvaliacaoForm,
    'unidade': UnidadeForm,
    'video': VideoForm,
    'arquivo': ArquivoForm,
    'questionario': QuestionarioForm,
    'questao': QuestaoForm,
    'alternativa': AlternativaForm,
}


def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


class Home(TemplateView):
    template_name = 'index.html'


@login_required
def registrosListView(request, modelo):
    """
    View responsável pelo tratamento de obtenção da lista de registros associados ao modelo fornecido
    """

    tituloPagina = modelo._meta.verbose_name_plural
    nomeLink = remover_acentos(modelo._meta.verbose_name.lower())

    search = request.GET.get('search')

    if search:
        search_fields = modelo.CustomMeta.search_fields
        filtro = reduce(or_, [Q(**{'{}__icontains'.format(f): search}) for f in search_fields], Q())
        objetos = modelo.objects.filter(filtro)

    else:
        listaObjetos = modelo.objects.all().order_by(modelo.CustomMeta.ordering_field)

        paginator = Paginator(listaObjetos, 5)

        page = request.GET.get('page')

        objetos = paginator.get_page(page)

    return render(
        request,
        'core/listaRegistro.html',
        {
            'objetos': objetos,
            'tituloPagina': tituloPagina,
            'nomeLink': nomeLink,
        }
    )


@login_required
def novoRegistroView(request, modelo):
    """
    View responsável pelo tratamento de adição de um novo registro associado ao modelo fornecido
    """

    nomeModelo = modelo._meta.verbose_name
    nomeModeloPlural = remover_acentos(modelo._meta.verbose_name_plural.lower())

    tituloPagina = f"Novo registro de {nomeModelo}"
    nomeLinkRedirecionamento = f"lista-{nomeModeloPlural}"

    formModelo = forms[remover_acentos(nomeModelo.lower())]

    if request.method == 'POST':
        form = formModelo(request.POST, request.FILES or None)

        if form.is_valid():
            objeto = form.save(commit=False)
            objeto.save()
            return redirect(
                nomeLinkRedirecionamento
            )
    else:
        form = formModelo()

    return render(
        request,
        'core/adicionaRegistro.html',
        {
            'form': form,
            'tituloPagina': tituloPagina
        }
    )


@login_required
def editaRegistroView(request, id, modelo):
    """
    View responsável pelo tratamento de edição de um registro associado ao modelo fornecido
    """

    nomeModelo = modelo._meta.verbose_name
    nomeModeloPlural = remover_acentos(modelo._meta.verbose_name_plural.lower())

    tituloPagina = f"Edição de registro de {nomeModelo}"
    nomeLinkRedirecionamento = f"lista-{nomeModeloPlural}"

    formModelo = forms[remover_acentos(nomeModelo.lower())]

    objeto = get_object_or_404(modelo, pk=id)

    form = formModelo(instance=objeto)

    if request.method == 'POST':
        form = formModelo(request.POST, instance=objeto)

        if(form.is_valid()):
            objeto.save()
            return redirect(
                nomeLinkRedirecionamento
            )
        else:
            return render(
                request,
                'core/editaRegistro.html',
                {
                    'form': form,
                    'tituloPagina': tituloPagina
                }
            )
    else:
        return render(
            request,
            'core/editaRegistro.html',
            {
                'form': form,
                'tituloPagina': tituloPagina
            }
        )


@login_required
def removeRegistroView(request, id, modelo):
    """
    View responsável pelo tratamento de remoção de um registro associado ao modelo fornecido
    """

    nomeModeloPlural = modelo._meta.verbose_name_plural.lower()
    nomeLinkRedirecionamento = f"lista-{nomeModeloPlural}"

    objeto = get_object_or_404(modelo, pk=id)
    objeto.delete()

    messages.info(
        request,
        'Registro removido com sucesso'
    )

    return redirect(
        nomeLinkRedirecionamento
    )