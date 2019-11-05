# users/urls.py
from django.urls import path
from .views import SignUpView, EditUserView, listaUsuariosView, \
    removeUsuarioView, novoUsuarioView

urlpatterns = [
    path('register/', SignUpView.as_view(), name='register'),
    path('edit/<int:id>', EditUserView, name='edituser'),
    path('lista-usuarios/', listaUsuariosView, name='lista-usuarios'),
    path('novo-usuario/', novoUsuarioView, name='novo-usuario'),
    path('remove-usuario/<int:id>', removeUsuarioView, name='remove-usuario'),

]