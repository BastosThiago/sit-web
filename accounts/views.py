from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from functools import reduce
from operator import or_
from django.db.models import Q
from django.contrib import messages

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from core.views import paginaInicialView, trata_usuario_sem_permissao, trata_erro_404


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy(paginaInicialView)
    template_name = 'signup.html'

    def form_valid(self, form):
        #save the new user first
        form.save()
        #get the username and password
        username = self.request.POST['username']
        password = self.request.POST['password1']
        #authenticate user then login
        user = authenticate(username=username, password=password)
        login(self.request, user)
        return HttpResponseRedirect('/area-usuario')


@login_required
def EditUserView(request, id):

    usuario = get_object_or_404(CustomUser, pk=id)
    form = CustomUserChangeForm(instance=usuario)

    perfil_aluno = False
    perfil_instrutor = False
    perfil_administrador = False

    # Avalia o perfil do usuário da requsição
    if request.user.tem_perfil_aluno():
        perfil_aluno = True

    if request.user.tem_perfil_administrador():
        perfil_administrador = True

    if request.user.tem_perfil_instrutor():
        perfil_instrutor = True

    if perfil_administrador:
        form.fields['first_name'].widget.attrs['readonly'] = False
        form.fields['last_name'].widget.attrs['readonly'] = False

    form.fields['perfil'].widget.attrs['disabled'] = True

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=usuario)

        if form.is_valid():
            usuario.save()
            return redirect('/')
        else:
            return render(
                request,
                'editUser.html',
                {
                    'form': form,
                    'usuario': usuario,
                    'perfil_aluno': perfil_aluno,
                    'perfil_administrador': perfil_administrador,
                    'perfil_instrutor': perfil_instrutor,
                }
            )
    else:
        return render(
            request,
            'editUser.html',
            {
                'form': form,
                'usuario': usuario,
                'perfil_aluno': perfil_aluno,
                'perfil_administrador': perfil_administrador,
                'perfil_instrutor': perfil_instrutor,
                'menu_inicio': False,
                'menu_meus_cursos': False,
                'menu_cadastros': False,
                'menu_relatorios': False,
                'menu_usuarios': True,

            }
        )


@login_required
def listaUsuariosView(request):
    """
    View responsável pelo tratamento de obtenção da lista de usuários do sistema
    """
    perfil_administrador = False

    if request.user.tem_perfil_administrador():
        perfil_administrador = True

        # Obtém o título a ser apresentado na página com base no nome do modelo
        tituloPagina = "Lista de usuários"

        # Verifica se algum filtro foi passado para obtenção dos registros
        try:
            search = request.GET.get('search')
        except:
            search = None

        # Verifica se na requisição de GET foi passado o parametro de pesquisa.
        # Caso sim, verifica o texto pesquisado nas informações do modelo
        if search:
            search_fields = ['username', 'first_name', 'last_name', 'email']
            filtro = reduce(or_, [Q(**{'{}__icontains'.format(f): search}) for f in search_fields], Q())
            objetos = CustomUser.objects.filter(filtro)

            objetos = objetos.filter(Q(perfil=1) | (Q(perfil=2))).order_by('username')

        # Caso não, obtém a lista de todos os objetos
        else:
            lista_objetos = CustomUser.objects.all().order_by('username')
            lista_objetos = lista_objetos.filter(Q(perfil=1) | (Q(perfil=2)))

            paginator = Paginator(lista_objetos, 10)

            page = request.GET.get('page')

            objetos = paginator.get_page(page)

        nao_tem_objetos = False
        if len(objetos) == 0:
            nao_tem_objetos = True

        return render(
            request,
            'usuarios-lista.html',
            {
                'objetos': objetos,
                'tituloPagina': tituloPagina,
                'perfil_administrador': perfil_administrador,
                'nao_tem_objetos': nao_tem_objetos,
                'menu_inicio': False,
                'menu_meus_cursos': False,
                'menu_cadastros': False,
                'menu_relatorios': False,
                'menu_usuarios': True,
            }
        )
    else:
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)


@login_required
def novoUsuarioView(request):
    """
    View responsável pelo tratamento de adição de um novo usuário
    """

    # Avalia o perfil do usuário da requsição
    if request.user.tem_perfil_administrador():
        perfil_administrador = True

        # Caso o método HTTP associado a requisição seja POST
        # Exibe o formulário com os dados já existentes, senão, um em branco
        if request.method == 'POST':
            form = CustomUserCreationForm(request.POST or None)

            if form.is_valid():
                objeto = form.save(commit=False)
                objeto.save()
                return redirect(
                    "/accounts/lista-usuarios"
                )
        else:
            form = CustomUserCreationForm()

        return render(
            request,
            'novo-usuario.html',
            {
                'form': form,
                'perfil_administrador': perfil_administrador,
                'menu_inicio': False,
                'menu_meus_cursos': False,
                'menu_cadastros': False,
                'menu_relatorios': False,
                'menu_usuarios': True,
            }
        )
    else:
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)


@login_required
def removeUsuarioView(request, id):
    """
    View responsável pelo tratamento de remoção de um registro de usuário
    """
    perfil_administrador = False

    # Avalia o perfil do usuário da requsição
    if request.user.tem_perfil_administrador():
        perfil_administrador = True

        # Obtém o objeto a ser removido e em caso de sucesso, o remove
        try:
            objeto = CustomUser.objects.filter(pk=id)[0]
        except:
            # Indica mensagem de sucesso na removação
            messages.info(
                request,
                'Falha ao remover o registro'
            )
            return HttpResponseRedirect(
                "/accounts/lista-usuarios"
            )

        try:
            objeto.delete()
            # Indica mensagem de sucesso na removação
            messages.info(
                request,
                'Registro removido com sucesso'
            )
        except:
            # Indica mensagem de sucesso na removação
            messages.info(
                request,
                'Falha ao remover o registro'
            )

        # Redireciona o usuário para a página da lista de registros
        return redirect(
            "/accounts/lista-usuarios"
        )
    else:
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)
