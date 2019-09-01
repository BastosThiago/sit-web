from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView

from .forms import CustomUserCreationForm, CustomUserChangeForm
from .models import CustomUser

class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('login')
    template_name = 'signup.html'

def EditUserView(request, id): # Edita uma tarefa já existente

    usuario = get_object_or_404(CustomUser, pk=id)
    form = CustomUserChangeForm(instance=usuario)

    if request.method == 'POST':
        form = CustomUserChangeForm(request.POST, instance=usuario)

        if(form.is_valid()):
            usuario.save()
            return redirect('/')
        else:
            return render(request, 'editUser.html', {'form': form, 'usuario': usuario})
    else:
        return render(request, 'editUser.html', {'form': form, 'usuario': usuario})