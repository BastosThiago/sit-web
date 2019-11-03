from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser
from core.views import paginaInicialView

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
        return HttpResponseRedirect('/area-usuario')  # User is not logged in on this page

def EditUserView(request, id): # Edita uma tarefa já existente

    usuario = get_object_or_404(CustomUser, pk=id)
    form = CustomUserChangeForm(instance=usuario)

    perfil_aluno = False
    perfil_instrutor = False
    perfil_administrador = False

    # Avalia o perfil do usuário da requsição
    if usuario.tem_perfil_aluno():
        perfil_aluno = True

    if usuario.tem_perfil_administrador():
        perfil_administrador = True

    if usuario.tem_perfil_instrutor():
        perfil_instrutor = True

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=usuario)

        if(form.is_valid()):
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
            }
        )
