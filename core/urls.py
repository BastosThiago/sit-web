"""todo_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from .views import *
from sistema_treinamentos.settings import STATIC_URL, STATIC_ROOT
from django.conf.urls.static import static

urlpatterns = [
    path('', Home.as_view()),

    path('cursos',                         cursosListView,                                 name='cursos'),
    path('informacoes-curso/<int:id>',     informacoesCursoView,                           name='informacoes-curso'),
    path('inscricao-curso/',               inscricaoCursoView,                             name='inscricao-curso'),
    path('conteudo-curso/<int:id>',        conteudoCursoView,                              name='conteudo-curso'),
    path('visualizacao-video/<int:id>',    visualizacaoVideoView,                          name='visualizacao-curso'),

    path('cadastros-categorias/',          registrosListView,  {'modelo': Categoria},      name='cadastros-categorias'),
    path('adiciona-categoria/',            novoRegistroView,   {'modelo': Categoria},      name='nova-categoria'),
    path('edita-categoria/<int:id>',       editaRegistroView,  {'modelo': Categoria},      name='edita-categoria'),
    path('remove-categoria/<int:id>',      removeRegistroView, {'modelo': Categoria},      name='remove-categoria'),

    path('cadastros-cursos/',              registrosListView,  {'modelo': Curso},          name='cadastros-cursos'),
    path('adiciona-curso/',                novoRegistroView,   {'modelo': Curso},          name='nova-curso'),
    path('edita-curso/<int:id>',           editaRegistroView,  {'modelo': Curso},          name='edita-curso'),
    path('remove-curso/<int:id>',          removeRegistroView, {'modelo': Curso},          name='remove-curso'),

    path('cadastros-inscricoes/',          registrosListView,  {'modelo': Inscricao},      name='cadastros-inscricoes'),
    path('adiciona-inscricao/',            novoRegistroView,   {'modelo': Inscricao},      name='nova-inscricao'),
    path('edita-inscricao/<int:id>',       editaRegistroView,  {'modelo': Inscricao},      name='edita-inscricao'),
    path('remove-inscricao/<int:id>',      removeRegistroView, {'modelo': Inscricao},      name='remove-inscricao'),

    path('cadastros-avaliacoes/',          registrosListView,  {'modelo': Avaliacao},      name='cadastros-avaliacoes'),
    path('adiciona-avaliacao/',            novoRegistroView,   {'modelo': Avaliacao},      name='nova-avaliacao'),
    path('edita-avaliacao/<int:id>',       editaRegistroView,  {'modelo': Avaliacao},      name='edita-avaliacao'),
    path('remove-avaliacao/<int:id>',      removeRegistroView, {'modelo': Avaliacao},      name='remove-avaliacao'),

    path('cadastros-unidades/',            registrosListView,  {'modelo': Unidade},        name='cadastros-unidades'),
    path('adiciona-unidade/',              novoRegistroView,   {'modelo': Unidade},        name='nova-unidade'),
    path('edita-unidade/<int:id>',         editaRegistroView,  {'modelo': Unidade},        name='edita-unidade'),
    path('remove-unidade/<int:id>',        removeRegistroView, {'modelo': Unidade},        name='remove-unidade'),

    path('cadastros-videos/',              registrosListView,  {'modelo': Video},          name='cadastros-videos'),
    path('adiciona-video/',                novoRegistroView,   {'modelo': Video},          name='nova-video'),
    path('edita-video/<int:id>',           editaRegistroView,  {'modelo': Video},          name='edita-video'),
    path('remove-video/<int:id>',          removeRegistroView, {'modelo': Video},          name='remove-video'),

    path('cadastros-arquivos/',            registrosListView,  {'modelo': Arquivo},        name='cadastros-arquivos'),
    path('adiciona-arquivo/',              novoRegistroView,   {'modelo': Arquivo},        name='nova-arquivo'),
    path('edita-arquivo/<int:id>',         editaRegistroView,  {'modelo': Arquivo},        name='edita-arquivo'),
    path('remove-arquivo/<int:id>',        removeRegistroView, {'modelo': Arquivo},        name='remove-arquivo'),

    path('cadastros-questionarios/',       registrosListView,  {'modelo': Questionario},   name='cadastros-questionarios'),
    path('adiciona-questionario/',         novoRegistroView,   {'modelo': Questionario},   name='nova-questionario'),
    path('edita-questionario/<int:id>',    editaRegistroView,  {'modelo': Questionario},   name='edita-questionario'),
    path('remove-questionario/<int:id>',   removeRegistroView, {'modelo': Questionario},   name='remove-questionario'),

    path('cadastros-questoes/',            registrosListView,  {'modelo': Questao},        name='cadastros-questoes'),
    path('adiciona-questao/',              novoRegistroView,   {'modelo': Questao},        name='nova-questao'),
    path('edita-questao/<int:id>',         editaRegistroView,  {'modelo': Questao},        name='edita-questao'),
    path('remove-questao/<int:id>',        removeRegistroView, {'modelo': Questao},        name='remove-questao'),
    
    path('cadastros-alternativas/',        registrosListView,  {'modelo': Alternativa},    name='cadastros-alternativas'),
    path('adiciona-alternativa/',          novoRegistroView,   {'modelo': Alternativa},    name='nova-alternativa'),
    path('edita-alternativa/<int:id>',     editaRegistroView,  {'modelo': Alternativa},    name='edita-alternativa'),
    path('remove-alternativa/<int:id>',    removeRegistroView, {'modelo': Alternativa},    name='remove-alternativa'),
    

] + static(STATIC_URL, document_root=STATIC_ROOT)