import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from unicodedata import normalize
from functools import reduce
from operator import or_
from django.db.models import Q, Min, Max
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from datetime import datetime
import json
from django.contrib.staticfiles import finders

from sistema_treinamentos.settings import MEDIA_ROOT
from .forms import *
from .models import *
from .render import render_to_pdf
from accounts.models import CustomUser

# Dicionário que relaciona o modelo com seu form
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


def trata_erro_404(request, exception):
    """
    Função para padronizar o tratamento do erro 404(não encontrado)
    """
    response = render(request, '404.html')
    response.status_code = 404
    return response


def trata_erro_500(request):
    """
    Função para padronizar o tratamento do erro 500(erro interno no servidor)
    """
    response = render(request, '500.html')
    response.status_code = 500
    return response


def trata_usuario_sem_permissao(request):
    """
    Função para padronizar o tratamento do erro 203(não autorizado)
    """
    response = render(request, '203.html')
    response.status_code = 203
    return response


def obtemListaConteudoCurso(course_id):
    """
      Função auxiliar monta uma lista contendo dicionários que indicam
      todo o conteúdo de um curso
    """
    lista = []

    try:
        # Obtém o curso de acordo com o ID fornecido
        curso = Curso.objects.get(pk=course_id)

        # Obtém as unidades associadas aos cursos
        unidades = Unidade.objects.filter(curso=curso)

        # Para cada unidade do curso, obtém os conteúdos(videos, arquivos ou questionários)
        # e os insere na lista
        for unidade in unidades:

            videos = Video.objects.filter(unidade=unidade).order_by('ordem')
            for video in videos:
                lista.append(dict({video.id: 'video'}))

            arquivos = Arquivo.objects.filter(unidade=unidade).order_by('ordem')
            for arquivo in arquivos:
                lista.append(dict({arquivo.id: 'arquivo'}))

            questionarios = Questionario.objects.filter(unidade=unidade).order_by('ordem')
            for questionario in questionarios:
                lista.append(dict({questionario.id: 'questionario'}))
    except:
        lista = []
    return lista


def obtemLinksConteudosCurso(curso_id, conteudo_nome, conteudo_id):
    """
      Função auxiliar que obtém o link do conteúdo anterior e do próximo
      conteúdo de um curso dado o curso e o conteúdo atual selecionado
    """

    try:
        # Obtém a lista completa de conteúdos do curso de acordo com o ID fornecido
        lista_conteudo_curso = obtemListaConteudoCurso(curso_id)

        # Obtém o indice atual da lista de acordo com o conteúdo fornecido
        indice = lista_conteudo_curso.index(dict({conteudo_id: conteudo_nome}))

        # Caso tenha encontrado o item na lista, obtém o link para o conteúdo anterior
        # e para o próximo conteúdo
        if indice >= 0:
            [[conteudo_id, conteudo_nome]] = lista_conteudo_curso[indice].items()

            if indice - 1 >= 0:
                conteudo_anterior = lista_conteudo_curso[indice - 1]
                [[conteudo_anterior_id, conteudo_anterior_nome]] = lista_conteudo_curso[indice - 1].items()
                conteudo_anterior_url = f"/visualizacao-{conteudo_anterior_nome}/{conteudo_anterior_id}"
            else:
                conteudo_anterior_url = ''

            if indice + 1 < len(lista_conteudo_curso):
                proximo_conteudo = lista_conteudo_curso[indice + 1]
                [[prox_conteudo_id, prox_conteudo_nome]] = lista_conteudo_curso[indice + 1].items()
                prox_conteudo_url = f"/visualizacao-{prox_conteudo_nome}/{prox_conteudo_id}"
            else:
                prox_conteudo_url = ''
    except:
        conteudo_anterior_url = ''
        prox_conteudo_url = ''

    return conteudo_anterior_url, prox_conteudo_url


def remover_acentos(txt):
    """
      Função auxiliar para remover caracteres especiais de uma string
    """
    return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


def paginaInicialView(request):
    """
      View responsável por fornecer o template da página inicial
    """
    # Obtém qual o perfil do usuário que acessou a página inicial do sistema
    return render(
        request,
        'home-page.html',
    )


@login_required
def registrosListView(request, modelo):
    """
    View responsável pelo tratamento de obtenção da lista de registros associados
    ao modelo fornecido
    """
    perfil_aluno = False
    perfil_instrutor = False
    perfil_administrador = False

    # Avalia o perfil do usuário da requsição
    if request.user.tem_perfil_aluno():
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)

    if request.user.tem_perfil_administrador():
        perfil_administrador = True

    if request.user.tem_perfil_instrutor():
        perfil_instrutor = True

    if modelo == Curso:
        lista_cursos = True
    else:
        lista_cursos = False

    # Obtém o título a ser apresentado na página com base no nome do modelo
    tituloPagina = modelo._meta.verbose_name_plural

    # Obtém o texto a ser atribuido no link
    nomeLink = remover_acentos(modelo._meta.verbose_name.lower())

    # Verifica se algum filtro foi passado para obtenção dos registros
    try:
        search = request.GET.get('search')
    except:
        search = None

    # Verifica se na requisição de GET foi passado o parametro de pesquisa.
    # Caso sim, verifica o texto pesquisado nas informações do modelo
    if search:
        search_fields = modelo.CustomMeta.search_fields
        filtro = reduce(or_, [Q(**{'{}__icontains'.format(f): search}) for f in search_fields], Q())
        objetos = modelo.objects.obtem_objetos_por_perfil_usuario(request.user).filter(filtro)

    # Caso não, obtém a lista de todos os objetos
    else:
        lista_objetos = modelo.objects.obtem_objetos_por_perfil_usuario(
            request.user
        ).order_by(
            modelo.CustomMeta.ordering_field
        )

        paginator = Paginator(lista_objetos, 10)

        page = request.GET.get('page')

        objetos = paginator.get_page(page)

    # Verifica se nenhum objeto foi obitido na consulta
    nao_tem_objetos = False
    if len(objetos) == 0:
        nao_tem_objetos = True

    return render(
        request,
        'core/registros-lista.html',
        {
            'objetos': objetos,
            'tituloPagina': tituloPagina,
            'nomeLink': nomeLink,
            'perfil_aluno': perfil_aluno,
            'perfil_administrador': perfil_administrador,
            'perfil_instrutor': perfil_instrutor,
            'lista_cursos': lista_cursos,
            'nao_tem_objetos': nao_tem_objetos,
            'menu_inicio': False,
            'menu_meus_cursos': False,
            'menu_cadastros': True,
            'menu_relatorios': False,
            'menu_usuarios': False,
            'menu_dados_cadastrais': False,
        }
    )



@login_required
def novoRegistroView(request, modelo):
    """
    View responsável pelo tratamento de adição de um novo registro associado ao modelo fornecido
    """

    perfil_aluno = False
    perfil_instrutor = False
    perfil_administrador = False

    # Avalia o perfil do usuário da requsição
    if request.user.tem_perfil_aluno():
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)

    if request.user.tem_perfil_administrador():
        perfil_administrador = True

    if request.user.tem_perfil_instrutor():
        perfil_instrutor = True

    # Caso o perfil do usuário da requisição seja de INSTRUTOR, não permite ao
    # mesmo manipular o cadastro de Categorias, Avaliações e Inscrições
    if perfil_instrutor:
        if modelo == Categoria or modelo == Avaliacao or modelo == Inscricao:
            # Chama tratamento padrão para usuário sem permissão
            return trata_usuario_sem_permissao(request)

    # Obtém os nomes associado ao modelo da requisição
    nomeModelo = modelo._meta.verbose_name
    nomeModeloPlural = remover_acentos(modelo._meta.verbose_name_plural.lower())

    # Monta o título a ser apresentado na página
    tituloPagina = f"Novo registro de {nomeModelo}"

    # Monta a informação do link de redirecionamento
    nomeLinkRedirecionamento = f"cadastros-{nomeModeloPlural}"

    # Caso o modelo seja de Curso e o perfil do usuário da requsição seja
    # de INSTRUTOR, remove o campo de nome do instrutor do cadastro, pois
    # neste caso, será o nome do próprio usuário
    if modelo == Curso:
        if perfil_instrutor:
            formModelo = CursoForm
        else:
            formModelo = CursoAdminForm
    else:
        # Obtém o form associado ao modelo
        formModelo = forms[remover_acentos(nomeModelo.lower())]

    # Caso o método HTTP associado a requisição seja POST
    # Exibe o formulário com os dados já existentes, senão, um em branco
    if request.method == 'POST':
        form = formModelo(data=request.POST, files=request.FILES or None, user=request.user)

        if form.is_valid():
            objeto = form.save(commit=False)

            # Caso seja a criação de um curso, atualiza o usuário
            # responsável por criar o curso
            if modelo == Curso:
                objeto.usuario = request.user

                if objeto.publicado == True:
                    objeto.data_publicado = datetime.now()

            if modelo == Video:
                if objeto.caminho != None:
                    objeto.video_interno = True
                else:
                    objeto.video_interno = False

            objeto.save()
            return redirect(
                nomeLinkRedirecionamento
            )
    else:
        form = formModelo(user=request.user)

    return render(
        request,
        'core/registro-adiciona.html',
        {
            'form': form,
            'tituloPagina': tituloPagina,
            'perfil_aluno': perfil_aluno,
            'nomeLinkRedirecionamento': nomeLinkRedirecionamento,
            'perfil_administrador': perfil_administrador,
            'perfil_instrutor': perfil_instrutor,
            'menu_inicio': False,
            'menu_meus_cursos': False,
            'menu_cadastros': True,
            'menu_relatorios': False,
            'menu_usuarios': False,
            'menu_dados_cadastrais': False,
        }
    )


@login_required
def editaRegistroView(request, id, modelo):
    """
    View responsável pelo tratamento de edição de um registro associado ao
    modelo fornecido
    """

    perfil_aluno = False
    perfil_instrutor = False
    perfil_administrador = False

    # Avalia o perfil do usuário da requsição
    if request.user.tem_perfil_aluno():
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)

    if request.user.tem_perfil_administrador():
        perfil_administrador = True

    if request.user.tem_perfil_instrutor():
        perfil_instrutor = True

    # Obtém os nomes associado ao modelo da requisição
    nomeModelo = modelo._meta.verbose_name
    nomeModeloPlural = remover_acentos(modelo._meta.verbose_name_plural.lower())

    # Caso o modelo manipulado seja de Curso, marca essa condição para que no
    # template associado a edição seja disponibilizado um botão para permitir
    # o acesso ao cadastro de conteúdos do curso
    if nomeModelo == "Curso":
        edicao_curso = True
    else:
        edicao_curso = False

    # Monta o título a ser apresentado na página
    tituloPagina = f"Edição de registro de {nomeModelo}"
    nomeLinkRedirecionamento = f"cadastros-{nomeModeloPlural}"

    # Obtém o objeto de acordo com seu ID
    try:
        objeto = modelo.objects.obtem_objetos_por_perfil_usuario(request.user).filter(pk=id)[0]

        publicado = None
        if modelo == Curso:
            publicado = objeto.publicado

    except:
        return trata_erro_404(request, None)

    # Caso o modelo seja de Curso e o perfil do usuário da requsição seja
    # de INSTRUTOR, remove o campo de nome do instrutor do cadastro, pois
    # neste caso, será o nome do próprio usuário
    if modelo == Curso:
        perfil_usuario_curso_instrutor = objeto.usuario.tem_perfil_instrutor()
        if perfil_usuario_curso_instrutor:
            formModelo = CursoForm
        else:
            formModelo = CursoAdminForm
    else:
        # Obtém o form associado ao modelo
        formModelo = forms[remover_acentos(nomeModelo.lower())]

    #Obtém o form associado ao objeto
    form = formModelo(instance=objeto, user=request.user)

    # Caso o método HTTP da requsição seja de POST, cria o form com os dados recebidos
    if request.method == 'POST':
        form = formModelo(data=request.POST, instance=objeto, user=request.user)

        # Caso o preenchimento do formulário seja válido, salva o objeto e
        # redireciona para a listagem de registros
        if(form.is_valid()):

            objeto = form.save(commit=False)

            # Caso seja a criação de um curso, atualiza o usuário
            # responsável por criar o curso
            if modelo == Curso:
                objeto.usuario = request.user

                if publicado is not None and publicado == False and objeto.publicado == True:
                    objeto.data_publicado = datetime.now()

            if modelo == Video:
                if objeto.caminho != None:
                    objeto.video_interno = True
                else:
                    objeto.video_interno = False

            objeto.save()

            return redirect(
                nomeLinkRedirecionamento
            )
        else:
            return render(
                request,
                'core/registro-edicao.html',
                {
                    'form': form,
                    'tituloPagina': tituloPagina,
                    'nomeLinkRedirecionamento': nomeLinkRedirecionamento,
                    'perfil_aluno': perfil_aluno,
                    'perfil_administrador': perfil_administrador,
                    'perfil_instrutor': perfil_instrutor,
                    'edicao_curso': edicao_curso,
                    'objeto': objeto,
                    'menu_inicio': False,
                    'menu_meus_cursos': False,
                    'menu_cadastros': True,
                    'menu_relatorios': False,
                    'menu_usuarios': False,
                    'menu_dados_cadastrais': False,
                }
            )
    else:
        return render(
            request,
            'core/registro-edicao.html',
            {
                'form': form,
                'tituloPagina': tituloPagina,
                'nomeLinkRedirecionamento': nomeLinkRedirecionamento,
                'perfil_aluno': perfil_aluno,
                'perfil_administrador': perfil_administrador,
                'perfil_instrutor': perfil_instrutor,
                'edicao_curso': edicao_curso,
                'objeto': objeto,
                'menu_inicio': False,
                'menu_meus_cursos': False,
                'menu_cadastros': True,
                'menu_relatorios': False,
                'menu_usuarios': False,
                'menu_dados_cadastrais': False,
            }
        )


@login_required
def removeRegistroView(request, id, modelo):
    """
    View responsável pelo tratamento de remoção de um registro associado ao
    modelo fornecido
    """

    perfil_aluno = False
    perfil_instrutor = False
    perfil_administrador = False

    # Avalia o perfil do usuário da requsição
    if request.user.tem_perfil_aluno():
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)

    if request.user.tem_perfil_administrador():
        perfil_administrador = True

    if request.user.tem_perfil_instrutor():
        perfil_instrutor = True

    nomeModeloPlural = modelo._meta.verbose_name_plural.lower()
    nomeLinkRedirecionamento = f"cadastros-{nomeModeloPlural}"

    # Obtém o objeto a ser removido e em caso de sucesso, o remove
    try:
        objeto = modelo.objects.obtem_objetos_por_perfil_usuario(request.user).filter(pk=id)[0]
    except:
        return trata_erro_404(request, None)

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
        nomeLinkRedirecionamento
    )


def obtem_classe_notas(nota_media):
    """
    Função auxiliar para informar a classe a ser utilizada na nota média de
    um curso
    """
    dict_classe_nota = {}
    dict_classe_nota['nota_0_5'] = ''
    dict_classe_nota['nota_1'] = ''
    dict_classe_nota['nota_1_5'] = ''
    dict_classe_nota['nota_2'] = ''
    dict_classe_nota['nota_2_5'] = ''
    dict_classe_nota['nota_3'] = ''
    dict_classe_nota['nota_3_5'] = ''
    dict_classe_nota['nota_4'] = ''
    dict_classe_nota['nota_4_5'] = ''
    dict_classe_nota['nota_5'] = ''

    if nota_media >= 0.25 and nota_media <= 0.75:
        dict_classe_nota['nota_1'] = 'half'
    if nota_media > 0.75 and nota_media <= 1.25:
        dict_classe_nota['nota_1'] = 'on'
    if nota_media > 1.25 and nota_media <= 1.75:
        dict_classe_nota['nota_1'] = 'on'
        dict_classe_nota['nota_2'] = 'half'
    if nota_media > 1.75 and nota_media <= 2.25:
        dict_classe_nota['nota_1'] = 'on'
        dict_classe_nota['nota_2'] = 'on'
    if nota_media > 2.25 and nota_media <= 2.75:
        dict_classe_nota['nota_1'] = 'on'
        dict_classe_nota['nota_2'] = 'on'
        dict_classe_nota['nota_3'] = 'half'
    if nota_media > 2.75 and nota_media <= 3.25:
        dict_classe_nota['nota_1'] = 'on'
        dict_classe_nota['nota_2'] = 'on'
        dict_classe_nota['nota_3'] = 'on'
    if nota_media > 3.25 and nota_media <= 3.75:
        dict_classe_nota['nota_1'] = 'on'
        dict_classe_nota['nota_2'] = 'on'
        dict_classe_nota['nota_3'] = 'on'
        dict_classe_nota['nota_4'] = 'half'
    if nota_media > 3.75 and nota_media <= 4.25:
        dict_classe_nota['nota_1'] = 'on'
        dict_classe_nota['nota_2'] = 'on'
        dict_classe_nota['nota_3'] = 'on'
        dict_classe_nota['nota_4'] = 'on'
    if nota_media > 4.25 and nota_media <= 4.75:
        dict_classe_nota['nota_1'] = 'on'
        dict_classe_nota['nota_2'] = 'on'
        dict_classe_nota['nota_3'] = 'on'
        dict_classe_nota['nota_4'] = 'on'
        dict_classe_nota['nota_5'] = 'half'
    if nota_media > 4.75:
        dict_classe_nota['nota_1'] = 'on'
        dict_classe_nota['nota_2'] = 'on'
        dict_classe_nota['nota_3'] = 'on'
        dict_classe_nota['nota_4'] = 'on'
        dict_classe_nota['nota_5'] = 'on'

    return dict_classe_nota


def cursosListView(request):
    """
    View responsável pelo tratamento de obtenção da lista de cursos
    cadastrados no sistema
    """

    # Obtém todos os cursos com o STATUS de PUPLICADO
    cursos = Curso.objects.filter(publicado=True).order_by('titulo')

    if cursos:

        try:
            search = request.GET.get('search')
        except:
            search = None

        if search:
            search_fields = Curso.CustomMeta.search_fields
            filtro = reduce(or_, [Q(**{'{}__icontains'.format(f): search}) for f in search_fields], Q())
            cursos = cursos.filter(filtro)

        else:

            paginator = Paginator(cursos, 5)

            page = request.GET.get('page')

            cursos = paginator.get_page(page)

    lista_cursos = []

    # Para cada curso obtido, monta um dicionário com algumas informações adicionais
    for curso in cursos:
        dict_curso = {}
        dict_curso['curso'] = curso
        dict_curso['categoria'] = curso.categoria.titulo
        dict_curso['numero_avaliacoes'] = curso.obtem_numero_avaliacoes()
        nota_media = curso.obtem_nota_media()
        dict_curso['nota_media'] = nota_media

        dict_curso['nota_1'] = ''
        dict_curso['nota_2'] = ''
        dict_curso['nota_3'] = ''
        dict_curso['nota_4'] = ''
        dict_curso['nota_5'] = ''

        if nota_media >= 0.25 and nota_media <= 0.75:
            dict_curso['nota_1'] = 'half'
        if nota_media > 0.75 and nota_media <= 1.25:
            dict_curso['nota_1'] = 'on'
        if nota_media > 1.25 and nota_media <= 1.75:
            dict_curso['nota_1'] = 'on'
            dict_curso['nota_2'] = 'half'
        if nota_media > 1.75 and nota_media <= 2.25:
            dict_curso['nota_1'] = 'on'
            dict_curso['nota_2'] = 'on'
        if nota_media > 2.25 and nota_media <= 2.75:
            dict_curso['nota_1'] = 'on'
            dict_curso['nota_2'] = 'on'
            dict_curso['nota_3'] = 'half'
        if nota_media > 2.75 and nota_media <= 3.25:
            dict_curso['nota_1'] = 'on'
            dict_curso['nota_2'] = 'on'
            dict_curso['nota_3'] = 'on'
        if nota_media > 3.25 and nota_media <= 3.75:
            dict_curso['nota_1'] = 'on'
            dict_curso['nota_2'] = 'on'
            dict_curso['nota_3'] = 'on'
            dict_curso['nota_4'] = 'half'
        if nota_media > 3.75 and nota_media <= 4.25:
            dict_curso['nota_1'] = 'on'
            dict_curso['nota_2'] = 'on'
            dict_curso['nota_3'] = 'on'
            dict_curso['nota_4'] = 'on'
        if nota_media > 4.25 and nota_media <= 4.75:
            dict_curso['nota_1'] = 'on'
            dict_curso['nota_2'] = 'on'
            dict_curso['nota_3'] = 'on'
            dict_curso['nota_4'] = 'on'
            dict_curso['nota_5'] = 'half'
        if nota_media > 4.75:
            dict_curso['nota_1'] = 'on'
            dict_curso['nota_2'] = 'on'
            dict_curso['nota_3'] = 'on'
            dict_curso['nota_4'] = 'on'
            dict_curso['nota_5'] = 'on'

        lista_cursos.append(dict_curso)

    return render(
        request,
        'core/cursos-lista.html',
        {
            'objetos': cursos,
            'lista_cursos': lista_cursos,
        }
    )


def informacoesCursoView(request, id):
    """
    View responsável pelo tratamento de apresentação das informações de um curso
    """

    # Inicializa algumas variáveis para utilização da função
    curso_sem_conteudo = False
    unidades = None
    avaliacoes = None
    aluno_inscrito_curso = False
    perfil_aluno = False
    usuario_anonimo = False
    nota_media_curso = "Sem nota"
    numero_unidades = 0
    numero_videos = 0
    numero_arquivos = 0
    numero_questionarios = 0
    numero_avaliacoes = 0

    numero_avaliacoes_nota_1 = 0
    numero_avaliacoes_nota_2 = 0
    numero_avaliacoes_nota_3 = 0
    numero_avaliacoes_nota_4 = 0
    numero_avaliacoes_nota_5 = 0

    percentual_nota_1 = 0
    percentual_nota_2 = 0
    percentual_nota_3 = 0
    percentual_nota_4 = 0
    percentual_nota_5 = 0

    classe_nota_1 = ''
    classe_nota_2 = ''
    classe_nota_3 = ''
    classe_nota_4 = ''
    classe_nota_5 = ''

    # Obtém o curso de acordo com o ID fornecido na requsição
    curso = get_object_or_404(Curso, pk=id, publicado=True)

    categoria = curso.categoria.titulo

    # Caso o usuário que criou o curso tenha o perfil de INSTRUTOR, o nome do
    # instrutor do curso será o nome do próprio usuário, Se não, será o nome
    # do instrutor cadastrado para o curso
    if curso.usuario.tem_perfil_instrutor():
        instrutor = curso.usuario.get_full_name()
    else:
        instrutor = curso.nome_instrutor

    numero_inscritos = curso.obtem_numero_inscritos()

    # Verifica se o usuário da requisição é de perfil ALUNO e se está inscrito
    # no curso acessado
    if not request.user.is_anonymous:
        if request.user.tem_perfil_aluno():
            perfil_aluno = True
            if Inscricao.objects.usuario_inscrito_curso(
                    usuario=request.user,
                    curso=curso
            ):
                aluno_inscrito_curso = True
    else:
        usuario_anonimo = True

    # Verifica se o curso tem algum conteúdo
    if curso.tem_conteudo():

        # Obtém a lista de unidades associadas ao curso
        unidades = Unidade.objects.filter(curso=curso)

        # Obtém as avaliações associadas ao curso
        avaliacoes = Avaliacao.objects.filter(curso=curso)

        numero_avaliacoes = avaliacoes.count()

        # Para cada avaliação do curso, verifica a nota
        for avaliacao in avaliacoes:

            if avaliacao.nota == 1:
                numero_avaliacoes_nota_1 = numero_avaliacoes_nota_1 + 1
            if avaliacao.nota == 2:
                numero_avaliacoes_nota_2 = numero_avaliacoes_nota_2 + 1
            if avaliacao.nota == 3:
                numero_avaliacoes_nota_3 = numero_avaliacoes_nota_3 + 1
            if avaliacao.nota == 4:
                numero_avaliacoes_nota_4 = numero_avaliacoes_nota_4 + 1
            if avaliacao.nota == 5:
                numero_avaliacoes_nota_5 = numero_avaliacoes_nota_5 + 1

        if numero_avaliacoes > 0:
            percentual_nota_1 = (numero_avaliacoes_nota_1 * 100) / numero_avaliacoes
            percentual_nota_2 = (numero_avaliacoes_nota_2 * 100) / numero_avaliacoes
            percentual_nota_3 = (numero_avaliacoes_nota_3 * 100) / numero_avaliacoes
            percentual_nota_4 = (numero_avaliacoes_nota_4 * 100) / numero_avaliacoes
            percentual_nota_5 = (numero_avaliacoes_nota_5 * 100) / numero_avaliacoes

        percentual_nota_1 = "{:.2f}".format(percentual_nota_1)
        percentual_nota_2 = "{:.2f}".format(percentual_nota_2)
        percentual_nota_3 = "{:.2f}".format(percentual_nota_3)
        percentual_nota_4 = "{:.2f}".format(percentual_nota_4)
        percentual_nota_5 = "{:.2f}".format(percentual_nota_5)

        # Obtém a nota média das avaliações associadas a curso(caso exista alguma)
        nota_media_curso = "SEM NOTA"
        if avaliacoes.count() > 0:
            nota_media_curso = curso.obtem_nota_media()
            nota_media_curso = "{:.1f}".format(nota_media_curso)

        numero_unidades = curso.obtem_unidades().count()
        numero_videos = curso.obtem_videos().count()
        numero_arquivos = curso.obtem_arquivos().count()
        numero_questionarios = curso.obtem_questionarios().count()

        if nota_media_curso is not None and nota_media_curso != "SEM NOTA":
            dict_classe_nota = obtem_classe_notas(float(nota_media_curso))

            classe_nota_1 = dict_classe_nota['nota_1']
            classe_nota_2 = dict_classe_nota['nota_2']
            classe_nota_3 = dict_classe_nota['nota_3']
            classe_nota_4 = dict_classe_nota['nota_4']
            classe_nota_5 = dict_classe_nota['nota_5']

    else:
        curso_sem_conteudo = True

    return render(
        request,
        'core/curso-informacoes.html',
        {
            'curso': curso,
            'categoria': categoria,
            'instrutor': instrutor,
            'numero_inscritos': numero_inscritos,
            'curso_sem_conteudo': curso_sem_conteudo,
            'perfil_aluno': perfil_aluno,
            'usuario_anonimo': usuario_anonimo,
            'aluno_inscrito_curso': aluno_inscrito_curso,
            'unidades': unidades,
            'avaliacoes': avaliacoes,
            'nota_media_curso': nota_media_curso,
            'numero_unidades': numero_unidades,
            'numero_videos': numero_videos,
            'numero_arquivos': numero_arquivos,
            'numero_questionarios': numero_questionarios,
            'numero_avaliacoes': numero_avaliacoes,
            'numero_avaliacoes_nota_1': numero_avaliacoes_nota_1,
            'numero_avaliacoes_nota_2': numero_avaliacoes_nota_2,
            'numero_avaliacoes_nota_3': numero_avaliacoes_nota_3,
            'numero_avaliacoes_nota_4': numero_avaliacoes_nota_4,
            'numero_avaliacoes_nota_5': numero_avaliacoes_nota_5,
            'percentual_nota_1': percentual_nota_1,
            'percentual_nota_2': percentual_nota_2,
            'percentual_nota_3': percentual_nota_3,
            'percentual_nota_4': percentual_nota_4,
            'percentual_nota_5': percentual_nota_5,
            'classe_nota_1': classe_nota_1,
            'classe_nota_2': classe_nota_2,
            'classe_nota_3': classe_nota_3,
            'classe_nota_4': classe_nota_4,
            'classe_nota_5': classe_nota_5,
        }
    )


@login_required
def inscricaoCursoView(request, id):
    """
    View responsável pelo tratamento de inscrição de um usuário no curso
    selecionado
    """

    # Permite inscrição no curso apenas para usuários de perfil ALUNO
    if request.user.tem_perfil_aluno():
        if request.method == 'GET':
            try:
                curso = get_object_or_404(Curso, pk=id)

                inscricao = Inscricao.objects.filter(curso=curso, usuario=request.user)

                if inscricao.count() == 0:
                    Inscricao.objects.create(curso=curso, usuario=request.user)

                return redirect(
                    f"/conteudo-curso/{curso.id}"
                )

            except:
                return trata_erro_404(request, None)
        else:
            return trata_usuario_sem_permissao(request)
    else:
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)


@login_required
def avaliacaoCursoView(request, id):
    """
    View responsável pelo tratamento de avaliacao de um curso
    """

    # Permite a avaliação de um curso apenas para usuário de perfil ALUNO
    if request.user.tem_perfil_aluno():

        try:
            curso = Curso.objects.get(pk=id)

            # Verifica se o usuário está inscrito no curso associado ao recurso acessado
            # Caso não esteja inscrito, retorna uma mensagem associada
            usuario_inscrito = Inscricao.objects.usuario_inscrito_curso(request.user, curso)
            if usuario_inscrito == False:
                # Chama tratamento padrão para usuário sem permissão
                return trata_usuario_sem_permissao(request)

            inscricao = Inscricao.objects.get(curso=curso, usuario=request.user)

            # Caso a requisição seja uma POST, atualiza a avaliação ou cria uma
            # nova caso não exista
            if request.method == 'POST':

                nota = int(request.POST.get('nota'))
                comentario = request.POST.get('comentario')

                try:
                    avaliacao_usuario = Avaliacao.objects.get(
                        curso=inscricao.curso,
                        usuario=request.user
                    )

                    avaliacao_usuario.nota = nota
                    avaliacao_usuario.comentario = comentario
                    avaliacao_usuario.save()

                except:
                    avaliacao_usuario = Avaliacao.objects.create(
                        curso=inscricao.curso,
                        usuario=request.user,
                        nota=nota,
                        comentario=comentario,
                        data_avaliacao=datetime.now()
                    )
        except:
            resposta = HttpResponse('Falha ao executar a ação.')
            resposta.status_code = 404
            return resposta

        resposta = HttpResponse('SUCESSO')
        resposta.status_code = 200

        return resposta

    else:
        # Chama tratamento padrão para usuário sem permissão
        resposta = HttpResponse('Usuário sem permissão para executar a ação.')
        resposta.status_code = 404
        return resposta


@login_required
def eliminaAvaliacaoView(request, id):
    """
    View responsável pelo tratamento de eliminação de uma avalição de um curso
    """
    # Permite que a avaliação de um curso seja removida apenas para usuário de perfil ALUNO
    if request.user.tem_perfil_aluno():

        try:
            # Obtém a instãncia de modelo a ser removida
            avaliacao = Avaliacao.objects.get(curso_id=id, usuario=request.user)

            avaliacao.delete()
        except:
            # Chama tratamento padrão para usuário sem permissão
            resposta = HttpResponse('Usuário sem permissão para executar a ação.')
            resposta.status_code = 404
            return resposta

        resposta = HttpResponse('SUCESSO')
        resposta.status_code = 200

        return resposta

    else:
        # Chama tratamento padrão para usuário sem permissão
        resposta = HttpResponse('Usuário sem permissão para a ação.')
        resposta.status_code = 404
        return resposta


def obtem_objeto_conteudo_pela_url(conteudo_url):
    """
    Função que obtém a instância de modelo de acordo com a URL fornecida
    """
    try:
        # Obtém o tipo de conteúdo e o id do conteúdo na URL fornecida
        str = conteudo_url.split('-')
        str = str[1].split('/')
        tipo_conteudo = str[0]
        id_conteudo = str[1]

        # De acordo com o tipo de conteúdo, obtém a instância de modelo associada
        objeto_conteudo = None
        if tipo_conteudo == 'video':
            objeto_conteudo = Video.objects.filter(id=id_conteudo)
        elif tipo_conteudo == 'arquivo':
            objeto_conteudo = Arquivo.objects.filter(id=id_conteudo)
        elif tipo_conteudo == 'questionario':
            objeto_conteudo = Questionario.objects.filter(id=id_conteudo)

        if objeto_conteudo.count() == 1:
            objeto_conteudo = objeto_conteudo[0]
        else:
            objeto_conteudo = None

        return objeto_conteudo
    except:
        return None


@login_required
def areaUsuarioView(request):
    """
    View responsável pelo tratamento de apresentação da area do usuário de
    acordo com seu perfil
    """

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

    # Caso o perfil do usuário da requisição seja de ALUNO
    if perfil_aluno:

        # Obtem último conteudo acessado pelo usuário
        dict_ultimo_conteudo = {}
        dict_ultimo_conteudo['objeto_ultimo_conteudo'] = None
        inscricao_ultimo_conteudo_acessado = Inscricao.objects.\
            obtem_url_ultimo_conteudo_acessado_usuario(
                usuario=request.user
            )

        # Caso tenha obtido o último conteúdo acessado pelo usuário, obtém a
        # instância de modelo associado ao mesmo e retorna
        if inscricao_ultimo_conteudo_acessado.count() == 1:
            url = inscricao_ultimo_conteudo_acessado[0].ultimo_conteudo_acessado
            dict_ultimo_conteudo['url'] = url
            objeto_ultimo_conteudo = obtem_objeto_conteudo_pela_url(url)

            dict_ultimo_conteudo[
                'objeto_ultimo_conteudo'] = objeto_ultimo_conteudo

            if objeto_ultimo_conteudo is not None:
                dict_ultimo_conteudo['curso_titulo'] = \
                    inscricao_ultimo_conteudo_acessado[0].curso.titulo
                dict_ultimo_conteudo['unidade'] = objeto_ultimo_conteudo.unidade.titulo

        return render(
            request,
            'core/area-usuario.html',
            {
                'dict_ultimo_conteudo': dict_ultimo_conteudo,
                'perfil_aluno': True,
                'menu_inicio': True,
                'menu_meus_cursos': False,
                'menu_cadastros': False,
                'menu_relatorios': False,
                'menu_usuarios': False,
                'menu_dados_cadastrais': False,
            }
        )

    else:
        # Caso o perfil do usuário da requisição seja de INSTRUTOR
        if perfil_instrutor:

            return render(
                request,
                'core/area-instrutor.html',
                {
                    'perfil_instrutor': True,
                    'menu_inicio': True,
                    'menu_meus_cursos': False,
                    'menu_cadastros': False,
                    'menu_relatorios': False,
                    'menu_usuarios': False,
                    'menu_dados_cadastrais': False,
                }
            )
        # Caso o perfil do usuário da requisição seja de ADMINISTRADOR
        if perfil_administrador:
            return render(
                request,
                'core/area-administrador.html',
                {
                    'perfil_administrador': True,
                    'menu_inicio': True,
                    'menu_meus_cursos': False,
                    'menu_cadastros': False,
                    'menu_relatorios': False,
                    'menu_usuarios': False,
                    'menu_dados_cadastrais': False,
                }
        )


@login_required
def meusCursosView(request):
    """
    View responsável pelo tratamento de apresentação dos cursos de um usuário
    """

    # Caso o perfil do usuário da requisição seja de ALUNO
    if request.user.tem_perfil_aluno():

        # Obtém todas as inscrições do usuário
        inscricoes_usuario = Inscricao.objects.filter(usuario=request.user)

        lista_cursos = []
        for inscricao in inscricoes_usuario:
            dict_curso = {}

            curso = Curso.objects.filter(
                id=inscricao.curso.id,
                publicado=True
            )

            # Verifica se algum filtro foi passado para obtenção dos registros
            try:
                search = request.GET.get('search')
            except:
                search = None

            if search:
                search_fields = Curso.CustomMeta.search_fields
                filtro = reduce(or_,
                                [Q(**{'{}__icontains'.format(f): search}) for f
                                 in search_fields], Q())
                curso = curso.filter(filtro)

            if curso.count() == 1:
                dict_curso['curso'] = curso[0]
                dict_curso['inscricao'] = inscricao

                dict_curso['categoria'] = curso[0].categoria.titulo

                percentual_andamento = "{:.1f}".format(
                    inscricao.percentual_andamento)
                dict_curso['percentual_andamento'] = percentual_andamento

                lista_cursos.append(dict_curso)

        nao_tem_cursos = False
        if len(lista_cursos) == 0:
            nao_tem_cursos = True
        return render(
            request,
            'core/meus-cursos.html',
            {
                'lista_cursos': lista_cursos,
                'nao_tem_cursos': nao_tem_cursos,
                'perfil_aluno': True,
                'menu_inicio': False,
                'menu_meus_cursos': True,
                'menu_cadastros': False,
                'menu_relatorios': False,
                'menu_usuarios': False,
                'menu_dados_cadastrais': False,
            }
        )

    else:
        # Caso o perfil do usuário da requisição seja de INSTRUTOR
        if request.user.tem_perfil_instrutor():

            # Obtém os cursos criados pelo instrutor
            cursos = Curso.objects.obtem_objetos_por_perfil_usuario(request.user)

            # Verifica se algum filtro foi passado para obtenção dos registros
            try:
                search = request.GET.get('search')
            except:
                search = None

            if search:
                search_fields = Curso.CustomMeta.search_fields
                filtro = reduce(or_,
                                [Q(**{'{}__icontains'.format(f): search}) for f
                                 in search_fields], Q())
                cursos = cursos.filter(filtro)

            nao_tem_cursos = False
            if len(cursos) == 0:
                nao_tem_cursos = True

            return render(
                request,
                'core/meus-cursos-instrutor.html',
                {
                    'cursos': cursos,
                    'nao_tem_cursos': nao_tem_cursos,
                    'perfil_aluno': False,
                    'perfil_instrutor': True,
                    'menu_inicio': False,
                    'menu_meus_cursos': True,
                    'menu_cadastros': False,
                    'menu_relatorios': False,
                    'menu_usuarios': False,
                    'menu_dados_cadastrais': False,
                }
            )
        else:
            # Chama tratamento padrão para usuário sem permissão
            return trata_usuario_sem_permissao(request)


@login_required
def conteudoCursoView(request, id):
    """
    View responsável pelo tratamento de apresentação do conteúdo do curso
    selecionado
    """

    curso = None

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

    usuario_inscricao = None
    curso_objeto_ultimo_conteudo = None
    situacao_aluno_curso = "Não definida"
    percentual_andamento = 0
    percentual_acertos = 0
    data_inicio = None
    data_conclusao = None
    data_ultimo_acesso = None

    lista_unidades = []

    avaliacao = None

    # Caso o perfil do usuário da requisição seja de ALUNO
    if perfil_aluno:

        # Obtém os cursos com o status de PUBLICADO
        curso = get_object_or_404(Curso, pk=id, publicado=True)

        # Verifica se o usuário está inscrito no curso associado ao recurso acessado
        # Caso não esteja inscrito, retorna uma mensagem associada
        usuario_inscrito = Inscricao.objects.usuario_inscrito_curso(
            request.user,
            curso
        )
        if usuario_inscrito == False:
            # Chama tratamento padrão para usuário sem permissão
            return trata_usuario_sem_permissao(request)

        usuario_inscricao = Inscricao.objects.filter(
            usuario=request.user,
            curso=curso
        )

        if usuario_inscricao.count == 0:
            # Chama tratamento padrão para usuário sem permissão
            return trata_usuario_sem_permissao(request)
        else:
            usuario_inscricao = usuario_inscricao[0]

        avaliacao = Avaliacao.objects.filter(curso=curso, usuario=request.user)
        if avaliacao.count() == 1:
            avaliacao = avaliacao[0]
        else:
            avaliacao = None

        curso_objeto_ultimo_conteudo = \
            obtem_objeto_conteudo_pela_url(
                usuario_inscricao.ultimo_conteudo_acessado
            )

    else:
        # Caso o perfil do usuário seja de INSTRUTOR, permite apenas a visualização
        # do conteúdo do curso caso o usuário seja o criador do curso
        if perfil_instrutor:
            try:
                curso = Curso.objects.get(pk=id, usuario=request.user)
            except:
                # Chama tratamento padrão para usuário sem permissão
                return trata_usuario_sem_permissao(request)
            pass
        else:
            curso = get_object_or_404(Curso, pk=id)

    # Caso tenha obtido o curso com sucesso, obtém seus conteúdos
    if curso:
        unidades = Unidade.objects.filter(curso=curso)

        for unidade in unidades:
            dict_unidade = {}
            lista_videos = []
            lista_arquivos = []
            lista_questionarios = []
            dict_unidade['unidade'] = unidade

            videos = Video.objects.filter(unidade=unidade)

            for video in videos:
                dict_video = {}
                dict_video['video'] = video
                usuario_video = UsuarioVideo.objects.filter(
                    usuario=request.user,
                    video=video
                )

                dict_video['assistido'] = False
                if usuario_video.count() == 1:
                    if usuario_video[0].assistido:
                        dict_video['assistido'] = True

                lista_videos.append(dict_video)
            dict_unidade['videos'] = lista_videos

            arquivos = Arquivo.objects.filter(unidade=unidade)

            for arquivo in arquivos:
                dict_arquivo = {}
                dict_arquivo['arquivo'] = arquivo

                usuario_arquivo = UsuarioArquivo.objects.filter(
                    usuario=request.user,
                    arquivo=arquivo
                )

                dict_arquivo['acessado'] = False
                if usuario_arquivo.count() == 1:
                    if usuario_arquivo[0].acessado:
                        dict_arquivo['acessado'] = True

                lista_arquivos.append(dict_arquivo)
            dict_unidade['arquivos'] = lista_arquivos

            questionarios = Questionario.objects.filter(unidade=unidade)

            for questionario in questionarios:
                dict_questionario = {}
                dict_questionario['questionario'] = questionario

                usuario_questionario = UsuarioQuestionario.objects.filter(
                    usuario=request.user,
                    questionario=questionario
                )

                dict_questionario['respondido'] = False
                if usuario_questionario.count() == 1:
                    if usuario_questionario[0].respondido:
                        dict_questionario['respondido'] = True

                lista_questionarios.append(dict_questionario)
            dict_unidade['questionarios'] = lista_questionarios

            lista_unidades.append(dict_unidade)

        # Verifica se o usuário da requisição é de perfil ALUNO e caso seja
        # obtém a inscrição do usuário curso
        if perfil_aluno:
            try:
                inscricao = Inscricao.objects.get(curso=curso, usuario=request.user)

                atualizaAndamentoCurso(curso, request.user)

                situacao_aluno_curso = inscricao.situacao
                percentual_andamento = "{:.1f}".format(inscricao.percentual_andamento)
                percentual_acertos = "{:.1f}".format(inscricao.percentual_acertos)
                data_inicio = inscricao.data_inscricao
                data_conclusao = inscricao.data_conclusao
                data_ultimo_acesso = inscricao.data_ultimo_conteudo_acessado
            except:
                inscricao = None

            if data_ultimo_acesso is None:
                data_ultimo_acesso = datetime.now()
                if inscricao is not None:
                    inscricao.data_ultimo_conteudo_acessado = data_ultimo_acesso
                    inscricao.save()

    return render(
        request,
        'core/curso-conteudo.html',
        {
            'curso': curso,
            'lista_unidades': lista_unidades,
            'avaliacao': avaliacao,
            'situacao_aluno_curso': situacao_aluno_curso,
            'percentual_andamento': percentual_andamento,
            'percentual_acertos': percentual_acertos,
            'data_inicio': data_inicio,
            'data_conclusao': data_conclusao,
            'data_ultimo_acesso': data_ultimo_acesso,
            'perfil_aluno': perfil_aluno,
            'usuario_inscricao': usuario_inscricao,
            'curso_objeto_ultimo_conteudo': curso_objeto_ultimo_conteudo,
            'perfil_aluno': perfil_aluno,
            'perfil_administrador': perfil_administrador,
            'perfil_instrutor': perfil_instrutor,
            'menu_inicio': False,
            'menu_meus_cursos': True,
            'menu_cadastros': False,
            'menu_relatorios': False,
            'menu_usuarios': False,
            'menu_dados_cadastrais': False,
        }
    )


@login_required
def atualizaAcessoConteudoView(request):
    """
    View responsável pelo tratamento de marcar que o usuário da requisição
    acessou um determinado conteúdo de um curso
    """

    # Permite esse tratamento apenas para usuários de perfil ALUNO

    if request.user.tem_perfil_aluno() == True:
        percentual_andamento = None
        percentual_acertos = None
        situacao_aluno = None
        try:
            if request.method == 'GET':

                # Verifica o tipo de conteúdo e o seu ID para atualizar
                # o modelo correto
                tipo_conteudo = request.GET['tipo_conteudo']
                id_conteudo = int(request.GET['id_conteudo'])
                conteudo_status = False
                if request.GET['conteudo_status'] == "true":
                    conteudo_status = True

                curso = None
                if tipo_conteudo == "video":
                    usuario_video = UsuarioVideo.objects.get_or_create(
                        usuario=request.user,
                        video_id=id_conteudo
                    )

                    usuario_video[0].assistido = conteudo_status
                    usuario_video[0].save()

                    curso = usuario_video[0].video.unidade.curso

                if tipo_conteudo == "arquivo":
                    usuario_arquivo = UsuarioArquivo.objects.get_or_create(
                        usuario=request.user,
                        arquivo_id=id_conteudo
                    )

                    usuario_arquivo[0].acessado = conteudo_status
                    usuario_arquivo[0].save()

                    curso = usuario_arquivo[0].arquivo.unidade.curso

                if tipo_conteudo == "questionario":
                    usuario_questionario = UsuarioQuestionario.objects.get_or_create(
                        usuario=request.user,
                        questionario_id=id_conteudo,
                    )

                    usuario_questionario[0].respondido = conteudo_status
                    usuario_questionario[0].save()

                    curso = usuario_questionario[0].questionario.unidade.curso

                # Atualiza percentual de andamento no curso para o usuário
                if curso is not None:
                    atualizaAndamentoCurso(
                        curso,
                        request.user
                    )

                try:
                    inscricao = Inscricao.objects.get(
                        curso=curso,
                        usuario=request.user
                    )
                    percentual_andamento = inscricao.percentual_andamento
                    percentual_acertos = inscricao.percentual_acertos
                    situacao_aluno = inscricao.situacao
                except:
                    pass
        except Exception as e:
            resposta = HttpResponse('FALHA')
            resposta.status_code = 404
            return resposta

        resposta = JsonResponse(
            {
                'percentual_andamento': percentual_andamento,
                'percentual_acertos': percentual_acertos,
                'situacao_aluno': situacao_aluno,
            }
        )
        resposta.status_code = 200

        return resposta

    else:
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)


@login_required
@never_cache
def visualizacaoVideoView(request, id):
    """
    View responsável pelo tratamento de apresentação do vídeo selecionado
    """

    # Obtém video associado ao ID fornecido
    video = get_object_or_404(Video, pk=id)

    tipo_video = ''
    tempo_corrente = 0
    caminho_video = ''
    usuario_video = None

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

    # Registra que o usuário acessou a página do vídeo(apenas para usuários de perfil ALUNO)
    if request.user.tem_perfil_aluno():
        perfil_aluno = True

        # Verifica se o usuário está inscrito no curso associado ao recurso acessado
        # Caso não esteja inscrito, retorna uma mensagem associada
        usuario_inscrito = Inscricao.objects.usuario_inscrito_curso(request.user, video.unidade.curso)
        if usuario_inscrito == False:
            # Chama tratamento padrão para usuário sem permissão
            return trata_usuario_sem_permissao(request)

        # Tenta obter ou cria a associação entre usuário e video
        try:
            usuario_video = UsuarioVideo.objects.get_or_create(
                usuario=request.user,
                video=video
            )
            usuario_video = usuario_video[0]
        except:
            return trata_erro_500(request)

        # Obtém as informações da associação entre usuário e video
        if usuario_video:
            tempo_corrente = usuario_video.tempo_corrente

    # Verifica o tipo de video para que o frontend possa realizar o tratamento adequado
    if video.video_interno:
        caminho_video = video.caminho.name
        tipo_video = 'interno'
    else:
        caminho_video = video.url
        if 'https://www.youtube.com/embed/' in caminho_video:
            tipo_video = 'youtube'
        else:
            if 'https://player.vimeo.com/' in caminho_video:
                tipo_video = 'vimeo'

    # Obtém as URLs associadas aos conteúdos anterior e próximo do video acessado
    conteudo_anterior_url, proximo_conteudo_url = obtemLinksConteudosCurso(
        video.unidade.curso.id,
        'video',
        video.id
    )

    # Obtém a lista de conteúdo do curso
    lista_conteudo_curso = obtemListaConteudoCurso(video.unidade.curso.id)

    # Obtém o indice atual da lista de acordo com o conteúdo fornecido
    indice = lista_conteudo_curso.index(dict({video.id: 'video'}))

    # Obtém o ID do conteúdo anterior ao atual
    conteudo_anterior_id = 0
    conteudo_anterior_nome = ""
    if indice - 1 >= 0:
        [[conteudo_anterior_id, conteudo_anterior_nome]] = lista_conteudo_curso[indice - 1].items()
        if conteudo_anterior_nome != 'video':
            conteudo_anterior_id = 0

    usuario_video_anterior = None
    usuario_video_anterior_id = 0
    if conteudo_anterior_id > 0:
        try:
            video_aux = Video.objects.get(pk=conteudo_anterior_id)
            usuario_video_anterior = UsuarioVideo.objects.get(
                video=video_aux,
                usuario=request.user
            )
            usuario_video_anterior_id = usuario_video_anterior.id
        except:
            usuario_video_anterior = None
            usuario_video_anterior_id = 0

    # Obtém o ID do próximo conteúdo ao atual
    proximo_conteudo_id = 0
    prox_conteudo_nome = ""
    if indice + 1 < len(lista_conteudo_curso):
        [[proximo_conteudo_id, prox_conteudo_nome]] = lista_conteudo_curso[indice + 1].items()
        if prox_conteudo_nome != 'video':
            proximo_conteudo_id = 0

    usuario_video_proximo = None
    usuario_video_proximo_id = 0
    if proximo_conteudo_id > 0:
        try:
            usuario_video_proximo = UsuarioVideo.objects.get(
                video_id=proximo_conteudo_id,
                usuario=request.user
            )
            usuario_video_proximo_id = usuario_video_proximo.id
        except:
            usuario_video_proximo = None
            usuario_video_proximo_id = 0

    # Caso tenha obtido as informações de associação entre usuário e video
    data_acesso = None
    data_assistido = None
    assistido = None
    if usuario_video != None:
        data_acesso = usuario_video.data_acesso
        data_assistido = usuario_video.data_assistido
        assistido = usuario_video.assistido
        usuario_video_id = usuario_video.id
        tempo_corrente = usuario_video.tempo_corrente
    else:
        usuario_video_id = 0
        tempo_corrente = 0

    if request.user.tem_perfil_aluno():
        # Atualiza percentual de andamento no curso para o usuário
        atualizaAndamentoCurso(
            video.unidade.curso,
            request.user
        )

        # Atualiza o último conteúdo acessado pelo usuário
        atualizaUltimoConteudoAcessado(
            request.user,
            usuario_video.video.unidade.curso,
            f"visualizacao-video/{video.id}"
        )

    # Caso a requisição seja via AJAX de uma página de video
    if request.is_ajax() and request.GET['origem'] == 'video':
        return JsonResponse(
            {
                'titulo_video': video.titulo,
                'caminho_video': caminho_video,
                'tempo_corrente': tempo_corrente,
                'tipo_video': tipo_video,
                'conteudo_anterior_url': conteudo_anterior_url,
                'proximo_conteudo_url': proximo_conteudo_url,
                'conteudo_anterior_nome': conteudo_anterior_nome,
                'prox_conteudo_nome': prox_conteudo_nome,
                'usuario_video_id': usuario_video_id,
                'data_acesso': data_acesso,
                'data_assistido': data_assistido,
                'assistido': assistido,
                'perfil_aluno': perfil_aluno,
                'perfil_administrador': perfil_administrador,
                'perfil_instrutor': perfil_instrutor,
                'menu_inicio': False,
                'menu_meus_cursos': True,
                'menu_cadastros': False,
                'menu_relatorios': False,
                'menu_usuarios': False,
                'menu_dados_cadastrais': False,
            }
        )
    else:
        nome_template = 'core/video-visualizacao.html'
        if request.is_ajax():
            nome_template = 'core/video-conteudo.html'
        return render(
            request,
            nome_template,
            {
                'video': video,
                'titulo_video': video.titulo,
                'usuario_video': usuario_video,
                'tipo_video': tipo_video,
                'tempo_corrente': tempo_corrente,
                'caminho_video': caminho_video,
                'conteudo_anterior_url': conteudo_anterior_url,
                'proximo_conteudo_url': proximo_conteudo_url,
                'conteudo_anterior_nome': conteudo_anterior_nome,
                'prox_conteudo_nome': prox_conteudo_nome,
                'usuario_video_anterior_id': usuario_video_anterior_id,
                'usuario_video_proximo_id': usuario_video_proximo_id,
                'data_acesso': data_acesso,
                'data_assistido': data_assistido,
                'assistido': assistido,
                'usuario_video_id': usuario_video_id,
                'url_corrente': f"/visualizacao-video/{video.id}",
                'perfil_aluno': perfil_aluno,
                'perfil_administrador': perfil_administrador,
                'perfil_instrutor': perfil_instrutor,
                'menu_inicio': False,
                'menu_meus_cursos': True,
                'menu_cadastros': False,
                'menu_relatorios': False,
                'menu_usuarios': False,
                'menu_dados_cadastrais': False,
            },
        )


def atualizaAndamentoCurso(curso, usuario):
    """
    View responsável por atualizar o percentual da andamento do curso para
    um dado usuário
    """

    # Caso o usuário tenha perfil de ALUNO
    if usuario.tem_perfil_aluno():
        try:

            # Obtém o percentual de andamento do usuário no curso
            percentual_andamento = curso.obtem_percentual_andamento_por_usuario(
                usuario
            )

            # Obtém o percentual de acertos do usuário no curso
            percentual_acertos = curso.obtem_percentual_acertos_por_usuario(
                usuario
            )

            # Obtém a inscrição do usuário para o curso
            inscricao_usuario = Inscricao.objects.get(
                usuario=usuario,
                curso=curso
            )

            inscricao_usuario.percentual_andamento = percentual_andamento
            inscricao_usuario.percentual_acertos = percentual_acertos

            # Atualiza a situação do usuário no curso
            if percentual_andamento >= 100:
                inscricao_usuario.data_conclusao = datetime.now()
                if percentual_acertos >= PERCENTUAL_ACERTOS_QUESTIONARIOS_APROVACAO:
                    inscricao_usuario.situacao = 'APROVADO'
                else:
                    inscricao_usuario.situacao = 'REPROVADO'
            else:
                inscricao_usuario.situacao = 'EM ANDAMENTO'
            inscricao_usuario.save()

        except:
            return None


def atualizaUltimoConteudoAcessado(usuario, curso, url):
    """
        View responsável por atualizar o último conteúdo acessado pelo aluno
    """
    # Obtém a inscrição do usuário no curso para atualizar o último conteudo acessado por ele
    try:
        inscricao = Inscricao.objects.get(usuario=usuario, curso=curso)
        inscricao.ultimo_conteudo_acessado = url
        inscricao.data_ultimo_conteudo_acessado = datetime.now()
        inscricao.save()
    except:
        pass


@login_required
@never_cache
def atualizaVideoUsuarioView(request):
    """
    View responsável pelo tratamento de atualização das informações dos videos
    acessados pelo usuário
    """
    resposta = HttpResponse('SUCESSO')
    resposta.status_code = 200

    # Caso o usuário tenha perfil de ALUNO
    if request.user.tem_perfil_aluno():
        if request.method == 'GET':
            try:

                # Obtém as informações da requisição para serem atualizadas
                # na associado do usuário com o video
                usuario_video_id = request.GET['usuario_video_id']
                tempo_corrente = request.GET['tempo_corrente']
                video_assistido = request.GET['video_assistido']

                usuario_video = UsuarioVideo.objects.get(pk=usuario_video_id)
                usuario_video.tempo_corrente = tempo_corrente
                if(video_assistido == 'true'):

                    usuario_video.assistido = True
                    usuario_video.data_assistido = datetime.now()
                usuario_video.save()

                # Atualiza percentual de andamento no curso para o usuário
                atualizaAndamentoCurso(
                    usuario_video.video.unidade.curso,
                    request.user
                )
            except:
                return resposta
    return resposta


@login_required
@never_cache
def obtemInformacoesVideoUsuarioView(request):
    """
    View responsável pelo tratamento de obter informações de um video
    """

    # Caso o usuário tenha perfil de ALUNO
    if request.user.tem_perfil_aluno():
        if request.method == 'GET':
            try:
                usuario_video_id = request.GET['usuario_video_id']

                usuario_video = UsuarioVideo.objects.get(pk=usuario_video_id)

            except:
                return JsonResponse({})
        return JsonResponse(
            {"tempo_corrente": usuario_video.tempo_corrente}
        )


@login_required
def visualizacaoArquivoView(request, id):
    """
    View responsável pelo tratamento de apresentação do arquivo selecionado
    """

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

    # Obtém o arquivo de acordo com o ID recebido
    arquivo = get_object_or_404(Arquivo, pk=id)

    # Verifica o perfil do usuário
    if request.user.tem_perfil_aluno():

        # Verifica se o usuário está inscrito no curso associado ao recurso acessado
        # Caso não esteja inscrito, retorna uma mensagem associada
        usuario_inscrito = Inscricao.objects.usuario_inscrito_curso(request.user, arquivo.unidade.curso)

        if usuario_inscrito == False:
            # Chama tratamento padrão para usuário sem permissão
            return trata_usuario_sem_permissao(request)

        # Atualiza percentual de andamento no curso para o usuário
        atualizaAndamentoCurso(
            arquivo.unidade.curso,
            request.user
        )

        # Atualiza o último conteúdo acessado pelo usuário
        atualizaUltimoConteudoAcessado(
            request.user,
            arquivo.unidade.curso,
            f"visualizacao-arquivo/{arquivo.id}"
        )

        # Marca na instância de modelo do Usuario x Arquivo que o mesmo foi acessado
        try:
            usuario_arquivo = UsuarioArquivo.objects.get_or_create(
                usuario=request.user,
                arquivo=arquivo
            )

            usuario_arquivo[0].data_acesso = datetime.now()
            usuario_arquivo[0].acessado = True
            usuario_arquivo[0].save()
        except:
            pass

    # Obtém as URLs do próximo e do conteúdo anterior ao arquivo acessado
    conteudo_anterior_url, proximo_conteudo_url = obtemLinksConteudosCurso(
        arquivo.unidade.curso.id,
        'arquivo',
        arquivo.id
    )

    # Verifica se o arquivo estático existe
    arquivo_existe = False
    if finders.find(arquivo.caminho.name) is not None:
        arquivo_existe = True

    if not request.is_ajax():
        template_name = 'core/arquivo-visualizacao.html'
    else:
        template_name ='core/arquivo-conteudo.html'

    return render(
        request,
        template_name,
        {
            'arquivo': arquivo,
            'conteudo_anterior_url': conteudo_anterior_url,
            'proximo_conteudo_url': proximo_conteudo_url,
            'arquivo_existe': arquivo_existe,
            'perfil_aluno': perfil_aluno,
            'perfil_administrador': perfil_administrador,
            'perfil_instrutor': perfil_instrutor,
            'menu_inicio': False,
            'menu_meus_cursos': True,
            'menu_cadastros': False,
            'menu_relatorios': False,
            'menu_usuarios': False,
            'menu_dados_cadastrais': False,
        },
    )


@login_required
def visualizacaoQuestionarioView(request, id):
    """
    View responsável pelo tratamento de apresentação do questionario selecionado
    """

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

    # Obtém o questionário de acordo com seu ID
    questionario = get_object_or_404(Questionario, pk=id)

    # Verifica o perfil do usuário
    if perfil_aluno:

        # Verifica se o usuário está inscrito no curso associado ao recurso acessado
        # Caso não esteja inscrito, retorna uma mensagem associada
        usuario_inscrito = Inscricao.objects.usuario_inscrito_curso(request.user, questionario.unidade.curso)
        if usuario_inscrito == False:
            # Chama tratamento padrão para usuário sem permissão
            return trata_usuario_sem_permissao(request)

        # Atualiza as informações de andamento do curso para o usuário
        atualizaAndamentoCurso(
            questionario.unidade.curso,
            request.user
        )

        # Atualiza o último conteúdo acessado pelo usuário
        atualizaUltimoConteudoAcessado(
            request.user,
            questionario.unidade.curso,
            f"visualizacao-questionario/{questionario.id}"
        )


    # Obtém a questões associadas ao questionário
    questoes = Questao.objects.filter(questionario=questionario).order_by('ordem')

    # Obtém as alternativas associadas as questões do questionário
    alternativas = Alternativa.objects.filter(questao__in=questoes).order_by('ordem')

    # Verifica se não existem questões no questionário
    questionario_sem_questoes = False
    if questoes.count() == 0:
        questionario_sem_questoes = True

    # Caso o usuário da requisição seja do perfil ALUNO, realiza tratamentos
    # para registrar respostas
    perfil_aluno = False
    alternativas_dict = {}
    usuario_questionario = None
    if request.user.tem_perfil_aluno():
        perfil_aluno = True
        if request.method == 'POST':

            numero_respostas_corretas = 0
            percentual_acertos = 0

            # Obtém a resposta para cada pergunta do questionário
            for chave, valor in request.POST.items():

                if chave == 'csrfmiddlewaretoken' or chave == 'enviar':
                    continue

                try:
                    # Obtém o ID da alternativa respondida
                    alternativa_id = request.POST.get(chave)

                    # Obtém a alternativa respondida
                    alternativa = Alternativa.objects.get(pk=alternativa_id)

                    # Verifica se a alternativa respondida é a correta, para então
                    # contabilizar o percentual de acertos no questionário
                    if(alternativa.correta == True):
                        numero_respostas_corretas = numero_respostas_corretas + 1

                    # Registra a resposta do usuário
                    try:
                        usuario_resposta = UsuarioResposta.objects.get_or_create(
                            usuario=request.user,
                            questao=alternativa.questao,
                        )
                        usuario_resposta = usuario_resposta[0]
                        usuario_resposta.alternativa = alternativa
                        usuario_resposta.save()

                    except:
                        return trata_erro_500(request)
                except:
                    return trata_erro_500(request)

            # Cálcula o percentual de acertos no questionário
            percentual_acertos = (numero_respostas_corretas / questoes.count()) * 100

            # Armazena o resultado total do questionário
            try:
                usuario_questionario = UsuarioQuestionario.objects.get_or_create(
                    usuario=request.user,
                    questionario=questionario,
                )
                usuario_questionario = usuario_questionario[0]
                usuario_questionario.percentual_acertos = percentual_acertos
                usuario_questionario.data_execucao = datetime.now()
                usuario_questionario.respondido = True
                usuario_questionario.save()
            except:
                return trata_erro_500(request)

        # Verifica se o usuário da requisição já respondeu ao questionário anteriormente.
        # Se sim, obtém as respostas para cada questão
        for alternativa in alternativas:
            usuario_respostas = UsuarioResposta.objects.filter(
                alternativa=alternativa,
                usuario=request.user
            )

            if(usuario_respostas.count() > 0):
                alternativas_dict[alternativa.id] = True
            else:
                alternativas_dict[alternativa.id] = False

        # Obtém o último resultado do usuário no questionário
        try:
            usuario_questionario = UsuarioQuestionario.objects.get(
                questionario=questionario,
                usuario=request.user,
            )
        except:
            usuario_questionario = None

    # Obtém as URLs do próximo e do conteúdo anterior ao questionário acessado
    conteudo_anterior_url, proximo_conteudo_url = obtemLinksConteudosCurso(
        questionario.unidade.curso.id,
        'questionario',
        questionario.id
    )

    # Caso o requsição não seja via AJAX
    post_ajax = False
    if not request.is_ajax():
        template_name = 'core/questionario-visualizacao.html'
        post_ajax = True
    else:
        template_name = 'core/questionario-conteudo.html'

    return render(
        request,
        template_name,
        {
            'questionario': questionario,
            'questoes': questoes,
            'alternativas': alternativas,
            'alternativas_dict': alternativas_dict,
            'usuario_questionario': usuario_questionario,
            'conteudo_anterior_url': conteudo_anterior_url,
            'proximo_conteudo_url': proximo_conteudo_url,
            'questionario_sem_questoes': questionario_sem_questoes,
            'post_ajax': post_ajax,
            'perfil_aluno': perfil_aluno,
            'perfil_administrador': perfil_administrador,
            'perfil_instrutor': perfil_instrutor,
            'menu_inicio': False,
            'menu_meus_cursos': True,
            'menu_cadastros': False,
            'menu_relatorios': False,
            'menu_usuarios': False,
            'menu_dados_cadastrais': False,
        },
    )


@login_required
def downloadConteudo(request, file_path, diretorio):
    """
      View responsável por permitir o download de algum conteúdo do curso
    """
    try:
        file_path = f"{MEDIA_ROOT}//{diretorio}//{file_path}"
        wrapper = FileWrapper(open(file_path, 'rb'))
        response = HttpResponse(wrapper, content_type='application/force-download')
        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
        return response
    except Exception as e:
        return trata_erro_500()


@login_required
def obtemCertificado(request, curso_id):
    """
      View responsável por gerar um certificado de participação ao usuário
    """
    try:
        # Obtém o usuário associado a requisição
        usuario = CustomUser.objects.get(pk=request.user.id)

        if usuario.tem_perfil_aluno():

            # Obtém a inscrição do usuário no curso
            inscricao = Inscricao.objects.get(usuario=request.user, curso_id=curso_id)

            contexto = {
                'usuario': usuario,
                'inscricao': inscricao,
                'request': request
            }

            pdf = render_to_pdf('core/certificado-conclusao.html', contexto)

            if pdf:
                response = HttpResponse(pdf, content_type='application/pdf')
                nome_arquivo = "certificado.pdf"
                content = "inline; filename=%s" % (nome_arquivo)
                download = request.GET.get("download")
                if download:
                    content = "attachment; filename=%s" % (nome_arquivo)
                response['Content-Disposition'] = content

                # Marca na inscrição do usuário que ele obteve o certificado
                inscricao.obteve_certificado = True
                inscricao.save()
                return response
            return trata_erro_500(request)
        else:
            return trata_usuario_sem_permissao(request)

    except:
      return trata_erro_500(request)


@login_required
def relatorioAcompanhamentoView(request):
    """
      View responsável por configurar um relatório de acompanhamento de um aluno
    """

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

    # Caso o usuário tenha perfil de administrador
    if perfil_administrador or perfil_instrutor:

        if perfil_administrador == True:
            # Obtém todos os usuários de pefil ALUNO
            usuarios = CustomUser.objects.filter(perfil=1).order_by('username')

        else:
            # Obtém o ID dos usuários que estão incritos nos cursos criados
            # pelo instrutor da requisição
            usuarios_ids = Inscricao.objects.filter(
                curso__usuario=request.user,
            ).values_list('usuario_id')

            usuarios = CustomUser.objects.filter(id__in=usuarios_ids)

        usuario = None
        inscricoes = None
        usuario_id = request.GET.get('usuario')

        # Obtém o ID do usuário para então obter suas inscrições nos cursos
        if usuario_id is not None:
            try:
                if perfil_administrador:
                    usuario = CustomUser.objects.get(pk=usuario_id)
                    inscricoes = Inscricao.objects.filter(usuario=usuario)
                else:
                    usuario = usuarios.filter(id=usuario_id)[0]
                    inscricoes = Inscricao.objects.filter(
                        usuario=usuario,
                        curso__usuario=request.user
                    )

            except:
                usuario = None

        nao_tem_usuarios = False
        if len(usuarios) == 0:
            nao_tem_usuarios = True

        nao_tem_inscricoes = False

        if usuario is not None:
            if inscricoes is None:
                nao_tem_inscricoes = True
            elif len(inscricoes) == 0:
                nao_tem_inscricoes = True

        if request.is_ajax():
            return render(
                request,
                'core/relatorio-conteudo.html',
                {
                    'usuario': usuario,
                    'inscricoes': inscricoes,
                    'arquivo': False,
                    'nao_tem_usuarios': nao_tem_usuarios,
                    'nao_tem_inscricoes': nao_tem_inscricoes,
                    'perfil_aluno': perfil_aluno,
                    'perfil_administrador': perfil_administrador,
                    'perfil_instrutor': perfil_instrutor,
                    'menu_inicio': False,
                    'menu_meus_cursos': False,
                    'menu_cadastros': False,
                    'menu_relatorios': True,
                    'menu_usuarios': False,
                    'menu_dados_cadastrais': False,
                }
            )
        else:
            return render(
                request,
                'core/relatorio-acompanhamento.html',
                {
                    'usuarios': usuarios,
                    'usuario': usuario,
                    'inscricoes': inscricoes,
                    'arquivo': False,
                    'nao_tem_usuarios': nao_tem_usuarios,
                    'nao_tem_inscricoes': nao_tem_inscricoes,
                    'perfil_aluno': perfil_aluno,
                    'perfil_administrador': perfil_administrador,
                    'perfil_instrutor': perfil_instrutor,
                    'menu_inicio': False,
                    'menu_meus_cursos': False,
                    'menu_cadastros': False,
                    'menu_relatorios': True,
                    'menu_usuarios': False,
                    'menu_dados_cadastrais': False,
                }
            )
    else:
        if perfil_aluno:
            inscricoes = Inscricao.objects.filter(usuario=request.user)

            nao_tem_usuarios = False
            nao_tem_inscricoes = False
            if len(inscricoes) == 0:
                nao_tem_inscricoes = True

            return render(
                request,
                'core/relatorio-acompanhamento.html',
                {
                    'usuarios': None,
                    'usuario': request.user,
                    'inscricoes': inscricoes,
                    'arquivo': False,
                    'nao_tem_usuarios': nao_tem_usuarios,
                    'nao_tem_inscricoes': nao_tem_inscricoes,
                    'perfil_aluno': perfil_aluno,
                    'perfil_administrador': perfil_administrador,
                    'perfil_instrutor': perfil_instrutor,
                    'menu_inicio': False,
                    'menu_meus_cursos': False,
                    'menu_cadastros': False,
                    'menu_relatorios': True,
                    'menu_usuarios': False,
                    'menu_dados_cadastrais': False,
                }
            )
            pass
        else:
            # Chama tratamento padrão para usuário sem permissão
            return trata_usuario_sem_permissao(request)


def relatorioUsuarioView(request):
    """
      View responsável por gerar um relatório de acompanhamento de um aluno
    """

    # Caso o usuário tenha perfil de administrador
    if request.user.tem_perfil_administrador() or request.user.tem_perfil_instrutor():
        nao_tem_usuarios = False
        nao_tem_inscricoes = False
        usuario = None
        inscricoes = None
        if request.method == 'GET':
            try:
                usuario_id = request.GET['usuario_id']

                usuario = CustomUser.objects.get(pk=usuario_id)
                inscricoes = Inscricao.objects.filter(usuario=usuario)

                if len(inscricoes) == 0:
                    nao_tem_inscricoes = True

            except:
                return JsonResponse({})

        return render(
            request,
            'core/relatorio-conteudo.html',
            {
                'usuario': usuario,
                'inscricoes': inscricoes,
                'nao_tem_usuarios': nao_tem_usuarios,
                'nao_tem_inscricoes': nao_tem_inscricoes,
                'arquivo': False,
            }
        )
    else:
        # Chama tratamento padrão para usuário sem permissão
        return trata_usuario_sem_permissao(request)


@login_required
def obtemRelatorio(request, usuario_id):
    """
      View responsável por gerar um arquivo PDF do relatório de acompanhamento
    """

    try:
        usuario = CustomUser.objects.get(pk=usuario_id)
        inscricoes = Inscricao.objects.filter(usuario=usuario)

        contexto = {
            'usuario': usuario,
            'inscricoes': inscricoes,
            'arquivo': True,
            'request': request,
            'nao_tem_usuarios': False,
            'nao_tem_inscricoes': False,
        }
        pdf = render_to_pdf('core/relatorio-conteudo.html', contexto)

        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            nome_arquivo = "relatorio.pdf"
            content = "inline; filename=%s" % (nome_arquivo)
            download = request.GET.get("download")
            if download:
                content = "attachment; filename=%s" % (nome_arquivo)
            response['Content-Disposition'] = content
            return response
        return trata_erro_500(request)
    except:
        return trata_erro_500(request)


@never_cache
def cadastroConteudoCursoView(request, id):
    """
    View responsável pelo tratamento cadastrar os conteúdos de um curso
    """

    perfil_aluno = False
    perfil_instrutor = False
    perfil_administrador = False

    # Avalia o perfil do usuário da requsição
    if request.user.tem_perfil_aluno():
        return trata_usuario_sem_permissao(request)

    if request.user.tem_perfil_administrador():
        perfil_administrador = True

    if request.user.tem_perfil_instrutor():
        perfil_instrutor = True

    curso = get_object_or_404(Curso, pk=id)

    unidades = curso.obtem_unidades()

    videos = Video.objects.filter(unidade__in=unidades).order_by('ordem')

    arquivos = Arquivo.objects.filter(unidade__in=unidades).order_by('ordem')

    questionarios = Questionario.objects.filter(unidade__in=unidades).order_by('ordem')

    questoes = Questao.objects.filter(questionario__in=questionarios).order_by('ordem')

    alternativas = Alternativa.objects.filter(questao__in=questoes).order_by('ordem')

    # Caso o método HTTP associado a requisição seja POST
    # Exibe o formulário com os dados já existentes, senão, um em branco
    response_data = {}
    if request.method == 'POST':

        response_data = {}
        response_data['conteudo_tipo'] = ""
        response_data['resultado'] = "Item salvo com sucesso."
        response_data['conteudo_id'] = 0

        objeto_ordem = 0

        try:

            conteudo_id = int(request.POST['conteudo_id'])
            conteudo_tipo = request.POST['conteudo_tipo']
            unidade_ordem = request.POST['unidade_ordem']

            response_data['conteudo_tipo'] = conteudo_tipo
            response_data['unidade-selector'] = f"unidade-{unidade_ordem}"

            # Tenta obter a unidade de acordo com sua ordem no curso
            unidade = Unidade.objects.filter(curso=curso, ordem=unidade_ordem)

            if conteudo_tipo != "unidade" and unidade.count() == 1:
                unidade = unidade[0]
            else:
                if conteudo_tipo != "unidade":
                    status_response = 500
                    response_data['resultado'] = "Falha ao salvar o item."
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

            dict_modelo = {
                'unidade': Unidade,
                'video': Video,
                'arquivo': Arquivo,
                'questionario': Questionario,
                'questao': Questao,
                'alternativa': Alternativa
            }

            modelo = dict_modelo[conteudo_tipo]
            formModelo = forms[remover_acentos(conteudo_tipo.lower())]

            max_ordem_objeto = 0
            objeto = None

            if conteudo_id > 0:
                # Obtém a instância do conteúdo
                try:
                    objeto = modelo.objects.get(pk=conteudo_id)
                except:
                    status_response = 500
                    response_data['resultado'] = "Falha ao salvar ao item."
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

            if conteudo_tipo == 'unidade':
                unidade_titulo = request.POST['titulo-unidade']
                unidade_descricao = request.POST['descricao-unidade']
                objeto_ordem = request.POST['unidade_ordem']

                dict_objeto = {
                    'csrfmiddlewaretoken': request.POST['csrfmiddlewaretoken'],
                    'curso': curso.id,
                    'titulo': unidade_titulo,
                    'descricao': unidade_descricao,
                    'ordem': objeto_ordem
                }

                if unidade_titulo == "":
                    response_data[f"titulo-unidade-{unidade_ordem}"] = 'O título da unidade é obrigatório'
                    response_data['resultado'] = "Falha ao salvar o item."
                    status_response = 500
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                # Tenta obter o objeto da ordem atual
                objeto_ordem_atual = modelo.objects.filter(
                    curso=curso,
                    ordem=objeto_ordem
                )

                max_ordem_objeto = modelo.objects.obtem_ultima_ordem(
                    curso
                )

            if conteudo_tipo == 'video' or conteudo_tipo == 'arquivo' or conteudo_tipo == 'questionario':
                objeto_ordem = request.POST['conteudo_ordem']
                conteudo_titulo = request.POST['titulo']

                if conteudo_titulo == "":
                    response_data[f"titulo-{conteudo_tipo}-{objeto_ordem}-unidade-{unidade_ordem}"] = f"O Título do {conteudo_tipo} é obrigatório."
                    response_data['resultado'] = "Falha ao salvar o item."
                    status_response = 500
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                max_ordem_objeto = modelo.objects.obtem_ultima_ordem(
                    unidade
                )

                # Tenta obter o objeto da ordem atual
                objeto_ordem_atual = modelo.objects.filter(
                    unidade=unidade,
                    ordem=objeto_ordem
                )

            # Monta dicionário com as informações do conteudo
            if conteudo_tipo == 'video':
                conteudo_url = request.POST['url']
                video_interno = False

                if request.POST['tipo-video'] == 'arquivo':
                    video_interno = True
                    conteudo_url = ''

                file_len = request.FILES.__len__()

                if (conteudo_url == None or len(conteudo_url) == 0) and \
                        ((objeto != None and objeto.caminho == "" and
                         file_len == 0) or (objeto == None and file_len == 0)):

                    response_data['resultado'] = "Configure uma URL ou selecione um arquivo de vídeo."
                    status_response = 500
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                dict_objeto = {
                    'csrfmiddlewaretoken': request.POST['csrfmiddlewaretoken'],
                    'unidade': unidade.id,
                    'titulo': conteudo_titulo,
                    'url': conteudo_url,
                    'video_interno': video_interno,
                    'ordem': objeto_ordem
                }

            if conteudo_tipo == 'arquivo':
                file_len = request.FILES.__len__()

                if (objeto != None and objeto.caminho == "" and file_len == 0) or (objeto == None and file_len == 0):
                    response_data[
                        f"path-{conteudo_tipo}-{objeto_ordem}-unidade-{unidade_ordem}"] = "Selecione um arquivo."
                    status_response = 500
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                dict_objeto = {
                    'csrfmiddlewaretoken': request.POST['csrfmiddlewaretoken'],
                    'unidade': unidade.id,
                    'titulo': conteudo_titulo,
                    'ordem': objeto_ordem
                }

            if conteudo_tipo == 'questionario':
                dict_objeto = {
                    'csrfmiddlewaretoken': request.POST['csrfmiddlewaretoken'],
                    'unidade': unidade.id,
                    'titulo': conteudo_titulo,
                    'ordem': objeto_ordem
                }

            if conteudo_tipo == 'questao':
                questionario_ordem = request.POST['questionario_ordem']
                questao_enunciado = request.POST['questao']
                objeto_ordem = request.POST['questao_ordem']

                response_data['questionario-selector'] = f"questionario-{questionario_ordem}-unidade-{unidade_ordem}"

                if questao_enunciado == "":
                    response_data[f"titulo-questao-{objeto_ordem}-questionario-{questionario_ordem}-unidade-{unidade_ordem}"] = f"Enunciado da questão é obrigatório."
                    response_data['resultado'] = "Falha ao salvar o item."
                    status_response = 500
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                questionario = Questionario.objects.filter(
                    unidade=unidade,
                    ordem=questionario_ordem
                )

                if questionario.count() == 0:
                    status_response = 500
                    response_data['resultado'] = "Falha ao salvar o item."
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                questao_questionario = questionario[0]

                dict_objeto = {
                    'csrfmiddlewaretoken': request.POST['csrfmiddlewaretoken'],
                    'questionario': questionario[0].id,
                    'enunciado': questao_enunciado,
                    'ordem': objeto_ordem
                }

                # Tenta obter o objeto da ordem atual
                objeto_ordem_atual = modelo.objects.filter(
                    questionario=questionario[0],
                    ordem=objeto_ordem
                )

                max_ordem_objeto = modelo.objects.obtem_ultima_ordem(
                    questionario[0]
                )

            if conteudo_tipo == 'alternativa':

                questionario_ordem = request.POST['questionario_ordem']
                questao_ordem = request.POST['questao_ordem']
                alternativa_descricao = request.POST['alternativa']

                response_data['questionario-selector'] = f"questionario-{questionario_ordem}-unidade-{unidade_ordem}"
                response_data['questao-selector'] = f"questao-{questao_ordem}-questionario-{questionario_ordem}-unidade-{unidade_ordem}"

                try:
                    request.POST['alternativa-correta']
                    alternativa_correta = True
                except:
                    alternativa_correta = False
                objeto_ordem = request.POST['alternativa_ordem']

                if alternativa_descricao == "":
                    response_data[f"titulo-alternativa-{objeto_ordem}-questao-{questao_ordem}-questionario-{questionario_ordem}-unidade-{unidade_ordem}"] = f"Descrição da alternativa é obrigatória."
                    response_data['resultado'] = "Falha ao salvar o item."
                    status_response = 500
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                questionario = Questionario.objects.filter(
                    unidade=unidade,
                    ordem=questionario_ordem
                )

                if questionario.count() == 0:
                    status_response = 500
                    response_data['resultado'] = "Falha ao salvar o item."
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                questao = Questao.objects.filter(
                    questionario=questionario[0],
                    ordem=questao_ordem
                )

                if questao.count() == 0:
                    status_response = 500
                    response_data['resultado'] = "Falha ao salvar o item."
                    return HttpResponse(
                        json.dumps(response_data), status=status_response
                    )

                questao_alternativa = questao[0]

                # Inicializa eventuais alternativas que estão marcadas como
                # correta para a questão da alternativa que estã sendo avaliada.
                if alternativa_correta:
                    alternativas = Alternativa.objects.filter(
                        questao=questao_alternativa,
                        correta=True
                    )

                    for alternativa in alternativas:
                        alternativa.correta = False
                        alternativa.save()

                dict_objeto = {
                    'csrfmiddlewaretoken': request.POST['csrfmiddlewaretoken'],
                    'questao': questao[0].id,
                    'descricao': alternativa_descricao,
                    'correta': alternativa_correta,
                    'ordem': objeto_ordem
                }

                # Tenta obter o objeto da ordem atual
                objeto_ordem_atual = modelo.objects.filter(
                    questao=questao[0],
                    ordem=objeto_ordem
                )

                max_ordem_objeto = modelo.objects.obtem_ultima_ordem(
                    questao[0]
                )

            # Caso o objeto já exista na base de dados
            if objeto != None:

                # Verifica se mudou a ordem do conteúdo
                if objeto.ordem != int(objeto_ordem):

                    # Caso existe uma instância do objeto para a ordem atual,
                    # inscrementa a ordem do mesmo
                    if objeto_ordem_atual.count() == 1:
                        objeto_aux = modelo.objects.get(pk=objeto_ordem_atual[0].id)
                        objeto_aux.ordem = max_ordem_objeto + 1
                        objeto_aux.save()

                # Verifica se foi enviado um novo arquivo no conteudo. Caso
                # sim, elemina a instância corrente do conteúdo para então
                # criar a nova
                if request.FILES.__len__() > 0:
                    objeto.delete()
                    form = formModelo(data=dict_objeto, files=request.FILES or None, user=request.user)

                    objeto = form.save()

                    if conteudo_tipo == 'video':
                        objeto.video_interno = video_interno
                        objeto.save()

                else:
                    # Atualiza as informações do Objeto
                    if conteudo_tipo == 'unidade':
                        objeto.curso = curso
                        objeto.titulo = dict_objeto['titulo']
                        objeto.descricao = dict_objeto['descricao']
                        objeto.ordem = dict_objeto['ordem']
                        objeto.save()

                    if conteudo_tipo == 'video':
                        objeto.unidade = unidade
                        objeto.titulo = dict_objeto['titulo']
                        objeto.url = dict_objeto['url']
                        objeto.video_interno = dict_objeto['video_interno']
                        if not objeto.video_interno:
                            objeto.caminho = None
                        objeto.ordem = dict_objeto['ordem']
                        objeto.save()

                    if conteudo_tipo == 'arquivo':
                        objeto.unidade = unidade
                        objeto.titulo = dict_objeto['titulo']
                        objeto.ordem = dict_objeto['ordem']
                        objeto.save()

                    if conteudo_tipo == 'questionario':
                        objeto.unidade = unidade
                        objeto.titulo = dict_objeto['titulo']
                        objeto.ordem = dict_objeto['ordem']
                        objeto.save()

                    if conteudo_tipo == 'questao':
                        objeto.questionario = questao_questionario
                        objeto.enunciado = dict_objeto['enunciado']
                        objeto.ordem = dict_objeto['ordem']
                        objeto.save()

                    if conteudo_tipo == 'alternativa':
                        objeto.questao = questao_alternativa
                        objeto.descricao = dict_objeto['descricao']
                        objeto.correta = dict_objeto['correta']
                        objeto.ordem = dict_objeto['ordem']
                        objeto.save()

            # Caso seja a criação de um novo objeto
            else:
                # Verifica se o objeto da ordem atual já existe para então
                # trocar sua ordem para permitir o cadastro do novo objeto
                if objeto_ordem_atual.count() == 1:
                    objeto_aux = modelo.objects.get(pk=objeto_ordem_atual[0].id)
                    objeto_aux.ordem = max_ordem_objeto + 1
                    objeto_aux.save()
                form = formModelo(data=dict_objeto, files=request.FILES or None, user=request.user)

                objeto = form.save()

                if conteudo_tipo == 'video':
                    objeto.video_interno = video_interno
                    objeto.save()

            if(conteudo_tipo == "video" or conteudo_tipo == "arquivo"):
                response_data['path_conteudo'] = objeto.caminho.name

            response_data['conteudo_id'] = objeto.id

        except Exception as e:
            status_response = 500
            response_data['resultado'] = "Falha ao salvar o item."
            return HttpResponse(
                json.dumps(response_data), status=status_response
            )

        status_response = 200
        return HttpResponse(
            json.dumps(response_data), status=status_response
        )

    else:
        teste = "a"

    return render(
        request,
        'core/curso-cadastro-conteudo.html',
        {
            'curso': curso,
            'unidades': unidades,
            'videos': videos,
            'arquivos': arquivos,
            'questionarios': questionarios,
            'questoes': questoes,
            'alternativas': alternativas,
            'perfil_aluno': perfil_aluno,
            'perfil_instrutor': perfil_instrutor,
            'perfil_administrador': perfil_administrador,
            'menu_inicio': False,
            'menu_meus_cursos': False,
            'menu_cadastros': True,
            'menu_relatorios': False,
            'menu_usuarios': False,
            'menu_dados_cadastrais': False,
        }
    )


@never_cache
def removeConteudoCursoView(request):
    """
    View responsável pelo tratamento remover um conteúdo de curso
    """

    if request.method == 'GET':

        tipo_conteudo = request.GET['tipo_conteudo']
        conteudo_id = request.GET['conteudo_id']
        id_resultado = request.GET['id_resultado']

        mensagem_erro = "Falha ao remover o item"

        status_response = 200
        response_data = {}

        dict_modelo = {
            'unidade': Unidade,
            'video': Video,
            'arquivo': Arquivo,
            'questionario': Questionario,
            'questao': Questao,
            'alternativa': Alternativa
        }

        modelo = dict_modelo[tipo_conteudo]
        objeto_reordenacao = None
        try:
            objeto = modelo.objects.get(pk=conteudo_id)

            if tipo_conteudo == "unidade":
                objeto_reordenacao = objeto.curso

            if tipo_conteudo == "video" or tipo_conteudo == "arquivo" or tipo_conteudo == "questionario":
                objeto_reordenacao = objeto.unidade

            if tipo_conteudo == "questao":
                objeto_reordenacao = objeto.questionario

            if tipo_conteudo == "alternativa":
                objeto_reordenacao = objeto.questao

            objeto.delete()
            modelo.objects.reordena_objetos(objeto_reordenacao)
        except:
            response_data[id_resultado] = mensagem_erro
            status_response = 500

        return HttpResponse(
            json.dumps(response_data), status=status_response
        )
    return HttpResponse()


@login_required
def cadastroConteudosView(request):
    """
    View responsável pelo tratamento de apresentação dos cursos de um usuário
    """
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


    # Verifica o perfil do usuário para obter o curso associado ao ID da requisição
    if perfil_aluno:
        return trata_usuario_sem_permissao(request)

    return render(
        request,
        'core/cadastros-conteudos.html',
        {
            'perfil_administrador': perfil_administrador,
            'perfil_instrutor': perfil_instrutor,
            'menu_inicio': False,
            'menu_meus_cursos': False,
            'menu_cadastros': True,
            'menu_relatorios': False,
            'menu_usuarios': False,
            'menu_dados_cadastrais': False,
        }
    )
