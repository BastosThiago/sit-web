from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse

from .models import *
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from .forms import *

# Create your views here.

class Home(TemplateView):
    template_name = 'base.html'


@login_required
def categoriasListView(request):

    search = request.GET.get('search')

    if search:

        categorias = Categoria.objects.filter(nome__icontains=search)

    else:
        categorias_list = Categoria.objects.all().order_by('nome')

        paginator = Paginator(categorias_list, 5)

        page = request.GET.get('page')

        categorias = paginator.get_page(page)

    return render(request,
                  'core/listCategories.html',
                  {'itens': categorias,
                   'titulo_pagina':'Categorias',
                   'nome_item': 'categoria'
                   })


def novaCategoriaView(request):
    if request.method == 'POST':
        form = CategoriaForm(request.POST)

        if form.is_valid():
            categoria = form.save(commit=False)
            categoria.save()
            return redirect('lista-categorias')
    else:
        form = CategoriaForm()

    return render(request,
                  'core/addCategory.html',
                  {'form': form,
                   'titulo_pagina': 'Adicione uma Categoria de curso'
                  })


def editaCategoria(request, id): # Edita uma categoria já existente

    categoria = get_object_or_404(Categoria, pk=id)
    form = CategoriaForm(instance=categoria)

    if request.method == 'POST':
        form = CategoriaForm(request.POST, instance=categoria)

        if(form.is_valid()):
            categoria.save()
            return redirect('lista-categorias')
        else:
            return render(request,
                          'core/editCategory.html',
                          {'form': form,
                           'task': categoria,
                           'titulo_pagina': 'Edite uma Categoria de curso'
                           })
    else:
        return render(request, 'core/editCategory.html', {'form': form, 'task': categoria})

@login_required
def removeCategoriaView(request, id): # Remove uma tarefa do banco de dados de acordo com o id da mesma fornecido na requisição
    categoria = get_object_or_404(Categoria, pk=id)
    categoria.delete()

    messages.info(request, 'Categoria removida com sucesso')
    return redirect('lista-categorias')