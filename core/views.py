from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from .models import *
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from .forms import *
from django.apps import apps

# Create your views here.

class Home(TemplateView):
    template_name = 'base.html'


@login_required
def categoriasListView(request):
    """
    View responsável pelo tratamento de obtenção da lista de Categorias e retorna-las para o template associado
    """

    tituloPagina = Categoria._meta.verbose_name_plural
    nomeObjeto = Categoria._meta.verbose_name_plural.lower()

    search = request.GET.get('search')

    if search:

        objetos = Categoria.objects.filter(nome__icontains=search)

    else:
        listaObjetos = Categoria.objects.all().order_by('nome')

        paginator = Paginator(listaObjetos, 5)

        page = request.GET.get('page')

        objetos = paginator.get_page(page)

    return render(
        request,
        'core/listaObjetos.html',
        {
            'objetos': objetos,
            'tituloPagina': tituloPagina,
            'nomeObjeto': nomeObjeto
        }
    )


@login_required
def novaCategoriaView(request):
    """
    View responsável pelo tratamento de adição de uma nova Categoria
    """

    tituloPagina = 'Adicione uma nova Categoria de curso'

    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            objeto = form.save(commit=False)
            objeto.save()
            return redirect(
                'lista-categorias'
            )
    else:
        form = CategoriaForm()

    return render(
        request,
        'core/adicionaObjeto.html',
        {
            'form': form,
            tituloPagina: tituloPagina
        }
    )


@login_required
def editaCategoriaView(request, id):
    """
    View responsável pelo tratamento de edição de uma Categoria existente
    """

    tituloPagina = 'Edite uma Categoria de curso'

    objeto = get_object_or_404(Categoria, pk=id)
    form = CategoriaForm(instance=objeto)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=objeto)

        if(form.is_valid()):
            objeto.save()
            return redirect(
                'lista-categorias'
            )
        else:
            return render(
                request,
                'core/editaObjeto.html',
                {'form': form,
                 tituloPagina: tituloPagina
                }
            )
    else:
        return render(
            request,
            'core/editaObjeto.html',
            {
                'form': form,
            }
        )


@login_required
def removeCategoriaView(request, id):
    """
    View responsável pelo tratamento de remoção de uma Categoria
    """

    objeto = get_object_or_404(Categoria, pk=id)
    objeto.delete()

    messages.info(
        request,
        'Categoria removida com sucesso'
    )

    return redirect(
        'lista-categorias'
    )