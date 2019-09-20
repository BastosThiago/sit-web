import os
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.generic.base import TemplateView
from unicodedata import normalize
from functools import reduce
from operator import or_
from django.db.models import Q, Min, Max
from django.http import HttpResponse
from wsgiref.util import FileWrapper
from datetime import datetime
from django.utils import timezone


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


def usuario_requisicao_aluno(request):
    """
      Função auxiliar que retorna se o usuário de uma requisição é do perfl ALUNO
    """
    if request.user.perfil == request.user.ALUNO:
        return True
    return False


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


class Home(TemplateView):
    """
      Classe responsável por fornecer o template da página inicial
    """
    #user = CustomUser.objects.get(pk=3)
    #curso = Curso.objects.get(pk=1)
    #Curso.objects.obtem_unidades_curso(curso)
    #Curso.objects.obtem_videos_curso(curso)
    #Curso.objects.obtem_questionarios_curso(curso)
    #Curso.objects.obtem_videos_assistindos_por_usuario(curso, user)
    #Curso.objects.obtem_questionarios_respondidos_por_usuario(curso, user)
    #Curso.objects.obtem_percentual_andamento_por_usuario(curso, user)
    #Curso.objects.obtem_percentual_acertos_por_usuario(curso, user)
    template_name = 'index.html'


@login_required
def registrosListView(request, modelo):
    """
    View responsável pelo tratamento de obtenção da lista de registros associados
    ao modelo fornecido
    """

    # Obtém o título a ser apresentado na página com base no nome do modelo
    tituloPagina = modelo._meta.verbose_name_plural

    # Obtém o texto a ser atribuido no link
    nomeLink = remover_acentos(modelo._meta.verbose_name.lower())


    search = request.GET.get('search')

    # Verifica se na requisição de GET foi passado o parametro de pesquisa.
    # Caso sim, verifica o texto pesquisado nas informações do modelo
    if search:
        search_fields = modelo.CustomMeta.search_fields
        filtro = reduce(or_, [Q(**{'{}__icontains'.format(f): search}) for f in search_fields], Q())
        objetos = modelo.objects.filter(filtro)

    # Caso não, obtém a lista de todos os objetos
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

    # Obtém os nomes associado ao modelo da requisição
    nomeModelo = modelo._meta.verbose_name
    nomeModeloPlural = remover_acentos(modelo._meta.verbose_name_plural.lower())

    # Monta o título a ser apresentado na página
    tituloPagina = f"Novo registro de {nomeModelo}"

    # Monta a informação do link de redirecionamento
    nomeLinkRedirecionamento = f"cadastros-{nomeModeloPlural}"

    # Obtém o form associado ao modelo
    formModelo = forms[remover_acentos(nomeModelo.lower())]

    # Caso o método HTTP associado a requisição seja POST
    # Exibe o formulário com os dados já existentes, senão, um em branco
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

    # Obtém os nomes associado ao modelo da requisição
    nomeModelo = modelo._meta.verbose_name
    nomeModeloPlural = remover_acentos(modelo._meta.verbose_name_plural.lower())

    # Monta o título a ser apresentado na página
    tituloPagina = f"Edição de registro de {nomeModelo}"
    nomeLinkRedirecionamento = f"cadastros-{nomeModeloPlural}"

    # Obtém o form associado ao modelo
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
            exibe_botao_inscricao = True
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

            if(inscricao.count() == 0):
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
    View responsável pelo tratamento de apresentação do conteúdo do curso selecionado
    """

    curso = get_object_or_404(Curso, pk=id)

    unidades = Unidade.objects.filter(curso=curso)

    videos = Video.objects.filter(unidade__in=unidades)

    arquivos = Arquivo.objects.filter(unidade__in=unidades)

    questionarios = Questionario.objects.filter(unidade__in=unidades)

    # Verifica se o usuário da requisição é do perfil ALUNO
    inscricao = None
    curso_concluido = False
    if usuario_requisicao_aluno(request):
        inscricao = Inscricao.objects.get(curso=curso, usuario=request.user)
        if inscricao.situacao != "EM ANDAMENTO":
            curso_concluido = True


    return render(
        request,
        'core/conteudoCurso.html',
        {
            'curso': curso,
            'unidades': unidades,
            'videos': videos,
            'arquivos': arquivos,
            'questionarios': questionarios,
            'inscricao': inscricao,
            'curso_concluido': curso_concluido,
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


    conteudo_anterior_url, proximo_conteudo_url = obtemLinksConteudosCurso(
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


def atualizaAndamentoCurso(curso, usuario):

    percentual_andamento= Curso.objects.obtem_percentual_andamento_por_usuario(
        curso,
        usuario
    )

    percentual_acertos = Curso.objects.obtem_percentual_acertos_por_usuario(
        curso,
        usuario
    )

    inscricao_usuario = Inscricao.objects.get(
        usuario=usuario,
        curso=curso
    )

    inscricao_usuario.percentual_andamento = percentual_andamento
    inscricao_usuario.percentual_acertos = percentual_acertos

    if percentual_andamento >= 100:
        inscricao_usuario.data_conclusao = datetime.now()
        if percentual_acertos >= 70:
            inscricao_usuario.situacao = 'APROVADO'
        else:
            inscricao_usuario.situacao = 'REPROVADO'

    inscricao_usuario.save()


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

            atualizaAndamentoCurso(usuario_video.video.unidade.curso)
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

    conteudo_anterior_url, proximo_conteudo_url = obtemLinksConteudosCurso(
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

        atualizaAndamentoCurso(questionario.unidade.curso, request.user)

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

    conteudo_anterior_url, proximo_conteudo_url = obtemLinksConteudosCurso(
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


def obtemCertificado(request, curso_id):

    usuario = CustomUser.objects.get(pk=request.user.id)
    inscricao = Inscricao.objects.get(usuario=request.user, curso_id=curso_id)

    contexto = {
        'usuario': usuario,
        'inscricao': inscricao,
        'request': request
    }
    pdf = render_to_pdf('core/certificado_conclusao.html', contexto)

    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        nome_arquivo = "certificado.pdf"
        content = "inline; filename='%s'" % (nome_arquivo)
        download = request.GET.get("download")
        if download:
            content = "attachment; filename='%s'" % (nome_arquivo)
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Erro ao gerar do certificado.", status=400)


def relatorioAcompanhamentoView(request):

    usuarios = CustomUser.objects.filter(perfil=1).order_by('username')

    usuario = None
    inscricoes = None
    usuario_id = request.GET.get('usuario')

    if usuario_id:
        try:
            usuario = CustomUser.objects.get(pk=usuario_id)
            inscricoes = Inscricao.objects.filter(usuario=usuario)
        except:
            usuario = None


    if request.is_ajax():
        return render(
            request,
            'core/conteudo-relatorio.html',
            {
                'usuario': usuario,
                'inscricoes': inscricoes,
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
            }
        )


def relatorioUsuarioView(request):

    if request.method == 'GET':
        try:
            usuario_id = request.GET['usuario_id']

            usuario = CustomUser.objects.get(pk=usuario_id)
            inscricoes = Inscricao.objects.filter(usuario=usuario)


        except:
            return JsonResponse({})

    return render(
        request,
        'core/conteudo-relatorio.html',
        {
            'usuario': usuario,
            'inscricoes': inscricoes,
        }
    )



