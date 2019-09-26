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
    curso = Curso.objects.get(pk=1)
    #Curso.obtem_unidades(curso)
    #Curso.obtem_videos(curso)
    #Curso.obtem_questionarios(curso)
    #UsuarioVideo.objects.obtem_videos_assistindos_por_usuario(curso, user)
    #UsuarioQuestionario.objects.obtem_questionarios_respondidos_por_usuario(curso, user)
    #Curso.objects.obtem_percentual_andamento_por_usuario(curso, user)
    #Curso.objects.obtem_percentual_acertos_por_usuario(curso, user)
    #curso.obtem_nota_media_curso()
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
        objetos = modelo.objects.filter(filtro)

    # Caso não, obtém a lista de todos os objetos
    else:
        listaObjetos = modelo.objects.all().order_by(modelo.CustomMeta.ordering_field)

        paginator = Paginator(listaObjetos, 5)

        page = request.GET.get('page')

        objetos = paginator.get_page(page)

    return render(
        request,
        'core/registros-lista.html',
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
        'core/registro-adiciona.html',
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

    # Obtém o objeto de acordo com seu ID
    objeto = get_object_or_404(modelo, pk=id)

    #Obtém o form associado ao objeto
    form = formModelo(instance=objeto)

    # Caso o método HTTP da requsição seja de POST, cria o form com os dados recebidos
    if request.method == 'POST':
        form = formModelo(request.POST, instance=objeto)

        # Caso o preenchimento do formulário seja válido, salva o objeto e
        # redireciona para a listagem de registros
        if(form.is_valid()):
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
                    'tituloPagina': tituloPagina
                }
            )
    else:
        return render(
            request,
            'core/registro-edicao.html',
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

    # Obtém o objeto a ser removido e em caso de sucesso, o remove
    objeto = get_object_or_404(modelo, pk=id)

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


@login_required
def cursosListView(request):
    """
    View responsável pelo tratamento de obtenção da lista de cursos cadastrados no sistema
    """

    # Verifica o perfil do usuário para retornar a lista de cursos
    cursos = None

    # Para usuários de perfil ALUNO, exibe todos os cursos com o status de PUBLICADOS.
    # Se não, retorna apenas os cursos criados pelo usuário corrente
    if request.user.tem_perfil_aluno():
        cursos = Curso.objects.filter(publicado=True).order_by('titulo')
    else:
        cursos = Curso.objects.filter(usuario=request.user).order_by('titulo')

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

    return render(
        request,
        'core/cursos-lista.html',
        {
            'objetos': cursos,
        }
    )


@login_required
def informacoesCursoView(request, id):
    """
    View responsável pelo tratamento de apresentação das informações de um curso
    """
    exibe_botao_inscricao = False
    exibe_botao_conteudo = False
    perfil_aluno = False
    avaliacao_usuario = None
    curso_sem_conteudo = False
    unidades = None
    avaliacoes = None
    nota_media_curso = None

    # Obtém o curso associado a requisição e verifica o perfil de usuário
    # para validar o curso a ser obtido
    if request.user.tem_perfil_aluno():
        curso = get_object_or_404(Curso, pk=id, publicado=True)
    else:
        curso = get_object_or_404(Curso, pk=id, usuario=request.user)

    # Verifica se o curso tem algum conteúdo
    if curso.tem_conteudo():

        # Obtém a lista de unidades associadas ao curso
        unidades = Unidade.objects.filter(curso=curso)

        # Obtém as avaliações associadas ao curso
        avaliacoes = Avaliacao.objects.filter(~Q(usuario=request.user), curso=curso)

        # Obtém a nota média das avaliações associadas a curso(caso exista alguma)
        nota_media_curso = "SEM NOTA"
        if avaliacoes.count() > 0:
            nota_media_curso = curso.obtem_nota_media()
            nota_media_curso = "{:.2f}".format(nota_media_curso)

        #verifica se o curso possui alguma unidade cadastrada
        if unidades.count() > 0:

            # Caso o usuário seja do pefil ALUNO
            if request.user.tem_perfil_aluno():

                perfil_aluno = True

                # Verifica se o usuário já está inscrito no curso acessado
                inscricao = Inscricao.objects.filter(curso=curso, usuario=request.user)

                if(inscricao.count() == 0):
                    exibe_botao_inscricao = True
                else:
                    exibe_botao_conteudo = True

                # Verifica se o usuário da requisição já avaliou o curso acessado
                try:
                    avaliacao_usuario = Avaliacao.objects.get(
                        curso=curso,
                        usuario=request.user
                    )
                except:
                    avaliacao_usuario = None
            else:
                exibe_botao_conteudo = True
    else:
        curso_sem_conteudo = True

    return render(
        request,
        'core/curso-informacoes.html',
        {
            'curso': curso,
            'curso_sem_conteudo': curso_sem_conteudo,
            'unidades': unidades,
            'avaliacoes': avaliacoes,
            'nota_media_curso': nota_media_curso,
            'avaliacao_usuario': avaliacao_usuario,
            'exibe_botao_inscricao': exibe_botao_inscricao,
            'exibe_botao_conteudo': exibe_botao_conteudo,
            'perfil_aluno': perfil_aluno
        }
    )


@login_required
def inscricaoCursoView(request):
    """
    View responsável pelo tratamento de inscrição de um usuário no curso selecionado
    """
    # Caso o usuário seja do pefil ALUNO
    if request.user.tem_perfil_aluno():
        resposta = "Falha ao realizar a inscrição."
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
    else:
        return HttpResponse("Usuário sem permissão para se inscrever em cursos.")


@login_required
def avaliacaoCursoView(request, id):
    """
    View responsável pelo tratamento de avaliacao de um curso
    """

    # Permite a avaliação de um curso apenas para usuário com perfil ALUNO
    if request.user.tem_perfil_aluno():

        try:
            curso = Curso.objects.get(pk=id)

            curso_sem_conteudo = not(curso.tem_conteudo())

            inscricao = Inscricao.objects.get(curso=curso, usuario=request.user)

            # Obtém as avaliações associadas ao curso
            avaliacoes = Avaliacao.objects.filter(~Q(usuario=request.user), curso=curso)

            avaliacao_usuario = None

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

            # Obtém a nota média de avaliação do curso
            nota_media_curso = curso.obtem_nota_media()
            nota_media_curso = "{:.2f}".format(nota_media_curso)
        except:
            curso = None
            inscricao = None
            avaliacoes = None

    return render(
        request,
        'core/avaliacao-conteudo.html',
        {
            'avaliacao_usuario': avaliacao_usuario,
            'avaliacoes': avaliacoes,
            'curso': curso,
            'curso_sem_conteudo': curso_sem_conteudo,
            'nota_media_curso': nota_media_curso,
        },
    )


@login_required
def conteudoCursoView(request, id):
    """
    View responsável pelo tratamento de apresentação do conteúdo do curso selecionado
    """

    curso = None
    perfil_aluno = False

    # Verifica o perfil do usuário para obter o curso associado ao ID da requisição
    if request.user.tem_perfil_aluno():
        perfil_aluno = True
        curso = get_object_or_404(Curso, pk=id, publicado=True)
    else:
        try:
            curso = Curso.objects.get(pk=id, usuario=request.user)
        except:
            curso = None

    # Caso tenha obtido o curso com sucesso, obtém seus conteúdos
    if curso:
        unidades = Unidade.objects.filter(curso=curso)

        videos = Video.objects.filter(unidade__in=unidades)

        arquivos = Arquivo.objects.filter(unidade__in=unidades)

        questionarios = Questionario.objects.filter(unidade__in=unidades)

        # Verifica se o usuário da requisição é de perfil ALUNO e caso seja
        # obtém a inscrição do usuário curso
        inscricao = None
        curso_concluido = False
        if perfil_aluno:
            try:
                inscricao = Inscricao.objects.get(curso=curso, usuario=request.user)
                if inscricao.situacao != "EM ANDAMENTO":
                    curso_concluido = True
            except:
                inscricao = None

    return render(
        request,
        'core/curso-conteudo.html',
        {
            'curso': curso,
            'unidades': unidades,
            'videos': videos,
            'arquivos': arquivos,
            'questionarios': questionarios,
            'inscricao': inscricao,
            'curso_concluido': curso_concluido,
            'perfil_aluno': perfil_aluno,
        }
    )


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

    # Registra que o usuário acessou a página do vídeo(apenas para usuários de perfil ALUNO)
    if request.user.tem_perfil_aluno():
        if video:

            # Tenta obter ou cria a associação entre usuário e video
            try:
                usuario_video = UsuarioVideo.objects.get(
                    video=video,
                    usuario=request.user
                )
            except:
                usuario_video = UsuarioVideo.objects.create(
                    video=video,
                    usuario=request.user
                )

        # Obtém as informações da associação entre usuário e video
        if usuario_video:
            tempo_corrente = usuario_video.tempo_corrente

    # Verifica o tipo de video para que o frontend possa realizar o tratamento adequado
    if video.video_interno:
        caminho_video = video.path.name
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
            usuario_video_anterior = UsuarioVideo.objects.get(video=video_aux, usuario=request.user)
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
            usuario_video_proximo = UsuarioVideo.objects.get(video_id=proximo_conteudo_id, usuario=request.user)
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
    else:
        usuario_video_id = 0

    # Caso a requisição seja via AJAX de uma página de video
    if request.is_ajax() and request.GET['origem'] == 'video':
        return JsonResponse(
            {
                'caminho_video': caminho_video,
                'tempo_corrente': usuario_video.tempo_corrente,
                'tipo_video': tipo_video,
                'conteudo_anterior_url': conteudo_anterior_url,
                'proximo_conteudo_url': proximo_conteudo_url,
                'conteudo_anterior_nome': conteudo_anterior_nome,
                'prox_conteudo_nome': prox_conteudo_nome,
                'usuario_video_id': usuario_video_id,
                'data_acesso': data_acesso,
                'data_assistido': data_assistido,
                'assistido': assistido
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
            },
        )



def atualizaAndamentoCurso(curso, usuario):
    """
    View responsável por atualizar o percentual da andamento do curso para um dado usuário
    """

    # Caso o usuário tenha perfil de ALUNO

    if usuario.tem_perfil_aluno():
        try:

            # Obtém o percentual de andamento do usuário no curso
            percentual_andamento= curso.obtem_percentual_andamento_por_usuario(
                usuario
            )

            # Obtém o percentual de acertos do usuário no curso
            percentual_acertos = curso.obtem_percentual_acertos_por_usuario(
                usuario
            )

            # Obtém a inscrição do usuário do curso
            inscricao_usuario = Inscricao.objects.get(
                usuario=usuario,
                curso=curso
            )

            inscricao_usuario.percentual_andamento = percentual_andamento
            inscricao_usuario.percentual_acertos = percentual_acertos

            # Atualiza a situação do usuário no curso
            if percentual_andamento >= 100:
                inscricao_usuario.data_conclusao = datetime.now()
                if percentual_acertos >= 70:
                    inscricao_usuario.situacao = 'APROVADO'
                else:
                    inscricao_usuario.situacao = 'REPROVADO'

            inscricao_usuario.save()

        except:
         return None


@login_required
@never_cache
def atualizaVideoUsuarioView(request):
    """
    View responsável pelo tratamento de atualização das informações dos videos acessados pelo usuário
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

    # Obtém o arquivo de acordo com o ID recebido
    arquivo = get_object_or_404(Arquivo, pk=id)

    # Obtém as URLs do próximo e do conteúdo anterior ao arquivo acessado
    conteudo_anterior_url, proximo_conteudo_url = obtemLinksConteudosCurso(
        arquivo.unidade.curso.id,
        'arquivo',
        arquivo.id
    )

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

    # Verifica se não existem questões no questionário
    questionario_sem_questoes = False
    if questoes.count() == 0:
        questionario_sem_questoes = True

    # Caso o usuário da requisição seja do perfil ALUNO, realiza tratamentos
    # para registrar respostas
    perfil_aluno = False
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
                except:
                    return None

            # Cálcula o percentual de acertos no questionário
            percentual_acertos = (numero_respostas_corretas / questoes.count()) * 100

            # Armazena o resultado total do questionário
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

            # Atualiza as informações de andamento do curso para o usuário
            atualizaAndamentoCurso(questionario.unidade.curso, request.user)

        # Verifica se o usuário da requisição já respondeu ao questionário anteriormente.
        # Se sim, obtém as respostas para cada questão
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
        },
    )


def downloadConteudo(request, file_path, diretorio):
    """
      View responsável por permitir o download de algum conteúdo do curso
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
                return response
            return HttpResponse("Erro ao gerar do certificado.", status=400)
        else:
            return HttpResponse("Usuário sem permissão para gerar certificado.", status=400)

    except:
      return HttpResponse("Erro ao gerar do certificado.", status=400)


def relatorioAcompanhamentoView(request):
    """
      View responsável por configurar um relatório de acompanhamento de um aluno
    """

    # Obtém todos os usuários de pefil ALUNO
    usuarios = CustomUser.objects.filter(perfil=1).order_by('username')

    usuario = None
    inscricoes = None
    usuario_id = request.GET.get('usuario')

    # Obtém o ID do usuário para então obter suas inscrições nos cursos
    if usuario_id:
        try:
            usuario = CustomUser.objects.get(pk=usuario_id)
            inscricoes = Inscricao.objects.filter(usuario=usuario)
        except:
            usuario = None


    if request.is_ajax():
        return render(
            request,
            'core/relatorio-conteudo.html',
            {
                'usuario': usuario,
                'inscricoes': inscricoes,
                'arquivo': False,
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
            }
        )


def relatorioUsuarioView(request):
    """
      View responsável por gerar um relatório de acompanhamento de um aluno
    """
    if request.method == 'GET':
        try:
            usuario_id = request.GET['usuario_id']

            usuario = CustomUser.objects.get(pk=usuario_id)
            inscricoes = Inscricao.objects.filter(usuario=usuario)

        except:
            return JsonResponse({})

    return render(
        request,
        'core/relatorio-conteudo.html',
        {
            'usuario': usuario,
            'inscricoes': inscricoes,
            'arquivo': False,
        }
    )


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
            'request': request
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
        return HttpResponse("Erro ao gerar do relatório.", status=400)
    except:
        return HttpResponse("Erro ao gerar do relatório.", status=400)



