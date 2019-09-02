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
    path('categorias', categoriasListView, name='lista-categorias'), # url raiz leva para lista de tarefas
    path('nova-categoria/', novaCategoriaView, name='nova-categoria'),        # url que apresenta um template para criação de uma nova tarefa
    path('edita-categoria/<int:id>', editaCategoriaView, name='edita-categoria'), # url que apresenta as informações de uma tarefa já existente para edição
    path('remove-categoria/<int:id>', removeCategoriaView, name='remove-categoria'),

]+ static(STATIC_URL, document_root=STATIC_ROOT)