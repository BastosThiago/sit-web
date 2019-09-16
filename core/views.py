from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache

from .models import *
from accounts.models import CustomUser
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from .forms import *
from unicodedata import normalize
from functools import reduce
from operator import or_
from django.db.models import Q, Min, Max


from datetime import datetime

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


def obtemListaConteudoCurso(course_id):

    lista = []
    curso = Curso.objects.get(pk=course_id)

    unidades = Unidade.objects.filter(curso=curso)

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

    return lista


def geraLinksConteudosCurso(curso_id, conteudo_nome, conteudo_id):

    lista_conteudo_curso = obtemListaConteudoCurso(curso_id)

    indice = lista_conteudo_curso.index(dict({conteudo_id: conteudo_nome}))

    # Caso tenha encontrado o item na lista
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

    return conteudo_anterior_url, prox_conteudo_url

def remover_acentos(txt):
    return normalize('NFKD', txt).encode('ASCII', 'ignore').decode('ASCII')


class Home(TemplateView):
    obtemListaConteudoCurso(1)
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
    nomeLinkRedirecionamento = f"cadastros-{nomeModeloPlural}"

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
    nomeLinkRedirecionamento = f"cadastros-{nomeModeloPlural}"

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
    nomeLinkRedirecionamento = f"cadastros-{nomeModeloPlural}"

    objeto = get_object_or_404(modelo, pk=id)
    objeto.delete()

    messages.info(
        request,
        'Registro removido com sucesso'
    )

    return redirect(
        nomeLinkRedirecionamento
    )


@login_required
def cursosListView(request):
    """
    View responsável pelo tratamento de obtenção da lista de cursos cadastrados no sistema
    """

    # Verifica o perfil do usuário para retornar a lista de cursos
    cursos = None
    if request.user.perfil == request.user.ALUNO:
        cursos = Curso.objects.filter(publicado=True).order_by('titulo')
    else:
        cursos = Curso.objects.filter(usuario=request.user).order_by('titulo')

    if cursos:
        search = request.GET.get('search')

        if search:
            search_fields = Curso.CustomMeta.search_fields
            filtro = reduce(or_, [Q(**{'{}__icontains'.format(f): search}) for f in search_fields], Q())
            cursos = cursos.filter(filtro)

        else:

            paginator = Paginator(cursos, 5)

            page = request.GET.get('page')

            cursos = paginator.get_page(page)

    return render(
        request,
        'core/listaCursos.html',
        {
            'objetos': cursos,
        }
    )


@login_required
def informacoesCursoView(request, id):
    """
    View responsável pelo tratamento de apresentação das informações de um curso
    """

    curso = get_object_or_404(Curso, pk=id)

    unidades = Unidade.objects.filter(curso=curso)

    avaliacoes = Avaliacao.objects.filter(curso=curso)

    exibe_botao_inscricao = False
    exibe_botao_conteudo  = False

    if request.user.perfil == request.user.ALUNO:
        inscricao = Inscricao.objects.filter(curso=curso, usuario=request.user)

        if(inscricao.count() == 0):
            exibe_botao_inscriacao = True
        else:
            exibe_botao_conteudo = True

    return render(
        request,
        'core/informacoesCurso.html',
        {
            'curso': curso,
            'unidades': unidades,
            'avaliacoes': avaliacoes,
            'exibe_botao_inscricao': exibe_botao_inscricao,
            'exibe_botao_conteudo': exibe_botao_conteudo,
        }
    )


@login_required
def inscricaoCursoView(request):
    """
    View responsável pelo tratamento de inscrição de um usuário no curso selecionado
    """
    resposta = "Falha ao realizar inscrição."
    if request.method == 'GET':
        try:
            curso_id = request.GET['curso_id']
            curso = Curso.objects.get(pk=curso_id)

            inscricao = Inscricao.objects.filter(curso=curso, usuario=request.user)

            if(inscricao):
                Inscricao.objects.create(curso=curso, usuario=request.user)
                resposta = "Inscrição realizada com sucesso."
            else:
                resposta ="Inscrição já realizada."

            return HttpResponse(resposta)
        except:
            return HttpResponse(resposta)
    else:
        return HttpResponse(resposta)


@login_required
def conteudoCursoView(request, id):
    """
    View responsável pelo tratamento de apresentação do conteúdo do curso selecioando
    """

    curso = get_object_or_404(Curso, pk=id)

    unidades = Unidade.objects.filter(curso=curso)

    videos = Video.objects.filter(unidade__in=unidades)

    arquivos = Arquivo.objects.filter(unidade__in=unidades)

    questionarios = Questionario.objects.filter(unidade__in=unidades)

    return render(
        request,
        'core/conteudoCurso.html',
        {
            'curso': curso,
            'unidades': unidades,
            'videos': videos,
            'arquivos': arquivos,
            'questionarios': questionarios,
        }
    )

@login_required
def visualizacaoVideoView(request, id):
    """
    View responsável pelo tratamento de apresentação do vídeo selecionado
    """

    video = get_object_or_404(Video, pk=id)

    # Registra que o usuário acessou a página do vídeo(caso ainda essa condição não tenha sido registrada)
    if video:

        try:
            usuario_video = UsuarioVideo.objects.get(video=video, usuario=request.user)
        except:
            usuario_video = UsuarioVideo.objects.create(video=video, usuario=request.user)

    tipo_video = 'arquivo'
    src_api_video = ''
    tempo_corrente = 0


    if usuario_video:
        tempo_corrente = usuario_video.tempo_corrente
        if usuario_video.assistido == True:
            tempo_corrente = 0

    if video:

        if video.video_interno:
            caminho_video = video.path
            tipo_video = 'interno'
        else:
            caminho_video = video.url
            if 'https://www.youtube.com/embed/' in caminho_video:
                tipo_video = 'youtube'
                src_api_video = 'http://www.youtube.com/player_api'
            else:
                if 'https://player.vimeo.com/' in caminho_video:
                    tipo_video = 'vimeo'
                    src_api_video = 'https://player.vimeo.com/api/player.js'


    conteudo_anterior_url, proximo_conteudo_url = geraLinksConteudosCurso(
        video.unidade.curso.id,
        'video',
        video.id
    )

    if not request.is_ajax():
        template_name = 'core/visualizacaoVideo.html'
    else:
        if tipo_video == 'vimeo':
            template_name ='vimeo_player.html'
        elif tipo_video =='youtube':
            template_name = 'youtube_player.html'
        else:
            template_name = 'video_interno_player.html'

    return render(
        request,
        template_name,
        {
            'video': video,
            'usuario_video': usuario_video,
            'tipo_video': tipo_video,
            'tempo_corrente': tempo_corrente,
            'caminho_video': caminho_video,
            'src_api_video': src_api_video,
            'conteudo_anterior_url': conteudo_anterior_url,
            'proximo_conteudo_url': proximo_conteudo_url,
        },
    )


@login_required
@never_cache
def atualizaVideoUsuarioView(request):
    """
    View responsável pelo tratamento de atualização das informações dos videos acessados pelo usuário
    """
    resposta = HttpResponse('SUCESSO')
    resposta.status_code = 200
    if request.method == 'GET':
        try:
            usuario_video_id = request.GET['usuario_video_id']
            tempo_corrente = request.GET['tempo_corrente']
            video_assistido = request.GET['video_assistido']

            usuario_video = UsuarioVideo.objects.get(pk=usuario_video_id)
            usuario_video.tempo_corrente = tempo_corrente
            assistido = bool(video_assistido)
            if(video_assistido == 'true'):

                usuario_video.assistido = True
                usuario_video.data_assistido = datetime.now()
            usuario_video.save()
        except:
            return resposta
    return resposta



@login_required
@never_cache
def obtemInformacoesVideoUsuarioView(request):
    """
    View responsável pelo tratamento de atualização das informações dos videos acessados pelo usuário
    """
    resposta = HttpResponse('SUCESSO')
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

    arquivo = get_object_or_404(Arquivo, pk=id)

    conteudo_anterior_url, proximo_conteudo_url = geraLinksConteudosCurso(
        arquivo.unidade.curso.id,
        'arquivo',
        arquivo.id
    )

    if not request.is_ajax():
        template_name = 'core/visualizacaoArquivo.html'
    else:
        template_name ='conteudo_arquivo.html'

    return render(
        request,
        template_name,
        {
            'arquivo': arquivo,
            'conteudo_anterior_url': conteudo_anterior_url,
            'proximo_conteudo_url': proximo_conteudo_url,
        },
    )


@login_required
def visualizacaoQuestionarioView(request, id):
    """
    View responsável pelo tratamento de apresentação do questionario selecionado
    """

    # Obtém o questionário de acordo com seu ID
    questionario = get_object_or_404(Questionario, pk=id)

    # Obtém a questões associadas ao questionário
    questoes = Questao.objects.filter(questionario=questionario).order_by('ordem')

    # Obtém as alternativas associadas as questões do questionário
    alternativas = Alternativa.objects.filter(questao__in=questoes).order_by('ordem')

    if request.method == 'POST':

        numero_respostas_corretas = 0
        percentual_acertos = 0
        for chave, valor in request.POST.items():

            if chave == 'csrfmiddlewaretoken' or chave == 'enviar':
                continue
            alternativa_id = request.POST.get(chave)

            alternativa = Alternativa.objects.get(pk=alternativa_id)

            if(alternativa.correta == True):
                numero_respostas_corretas = numero_respostas_corretas + 1

            try:
                usuario_resposta = UsuarioResposta.objects.get(
                    questao=alternativa.questao,
                    usuario=request.user
                )

                usuario_resposta.alternativa = alternativa
                usuario_resposta.save()

            except:
                usuario_resposta = UsuarioResposta.objects.create(
                    alternativa=alternativa,
                    questao=alternativa.questao,
                    usuario=request.user
                )

        percentual_acertos = (numero_respostas_corretas / questoes.count()) * 100

        try:
            usuario_questionario = UsuarioQuestionario.objects.get(
                questionario=questionario,
                usuario=request.user,
            )

            usuario_questionario.percentual_acertos = percentual_acertos
            usuario_questionario.data_execucao = datetime.now()
            usuario_questionario.save()
        except:
            usuario_questionario = UsuarioQuestionario.objects.create(
                questionario=questionario,
                usuario=request.user,
                percentual_acertos=percentual_acertos,
                data_execucao=datetime.now()
            )


    # Verifica se o usuário corrente já respondeu ao questionário
    alternativas_dict = {}
    for alternativa in alternativas:
        usuario_respostas = UsuarioResposta.objects.filter(
            alternativa=alternativa,
            usuario=request.user
        )

        if(usuario_respostas.count() > 0):
            alternativas_dict[alternativa.id] = True
        else:
            alternativas_dict[alternativa.id] = False

    # Verifca se o usuário corrente já respondeu ao questinário
    try:
        usuario_questionario = UsuarioQuestionario.objects.get(
            questionario=questionario,
            usuario=request.user,
        )
    except:
        usuario_questionario = None

    conteudo_anterior_url, proximo_conteudo_url = geraLinksConteudosCurso(
        questionario.unidade.curso.id,
        'questionario',
        questionario.id
    )

    post_ajax = False
    if not request.is_ajax():
        template_name = 'core/visualizacaoQuestionario.html'
        post_ajax = True
    else:
        template_name = 'conteudo_questionario.html'

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
            'post_ajax': post_ajax,
        },
    )


from django.http import HttpResponse
from wsgiref.util import FileWrapper
from sistema_treinamentos.settings import MEDIA_ROOT

import os

def downloadConteudo(request, file_path, diretorio):
    """
    e.g.: file_path = '/tmp/file.pdf'
    """
    try:
        file_path = f"{MEDIA_ROOT}\\{diretorio}\\{file_path}"
        wrapper = FileWrapper(open(file_path, 'rb'))
        response = HttpResponse(wrapper, content_type='application/force-download')
        response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
        return response
    except Exception as e:
        return None