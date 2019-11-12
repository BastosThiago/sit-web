# users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser

class CustomAuthenticationForm(AuthenticationForm):
    email = forms.CharField(label='Endereço de E-mail', max_length=50,
                            required=True)

    class Meta(AuthenticationForm):
        model = CustomUser
        #fields = ('username', 'password', 'email')
        fields = ('email', 'password', )
        exclude = ('username')

class CustomUserCreationForm(UserCreationForm):
    first_name = forms.CharField(label="Nome", max_length=30, required=True)
    last_name = forms.CharField(label="Sobrenome", max_length=30, required=True)
    email = forms.CharField(label='Endereço de E-mail', max_length=50, required=True)

    class Meta(UserCreationForm):
        model = CustomUser
        #fields = ('username', 'first_name', 'last_name', 'email', 'perfil')
        fields = ('email', 'first_name', 'last_name', 'perfil')


class CustomUserChangeForm(UserChangeForm):
    def __init__(self, *args, **kwargs):
        super(UserChangeForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        if instance and instance.pk:
            self.fields['first_name'].widget.attrs['readonly'] = True
            self.fields['last_name'].widget.attrs['readonly'] = True
            self.fields['perfil'].widget.attrs['readonly'] = True

    password = None

    class Meta(UserChangeForm):
        model = CustomUser
        fields = ('first_name', 'last_name', 'perfil', 'email',)
