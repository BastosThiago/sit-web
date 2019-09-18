# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=30, required=True)
    last_name = forms.CharField(label="Sobrenome", max_length=30, required=True)
    email = forms.CharField(label='Endereço de E-mail', max_length=50, required=True)

    class Meta(UserCreationForm):
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'perfil')


class CustomUserChangeForm(UserChangeForm):
    password = None
    class Meta(UserChangeForm):
        model = CustomUser
        fields = ('email',)