from django import forms
from django.contrib.auth.forms import \
    UserCreationForm, UserChangeForm, AuthenticationForm
from .models import CustomUser


class CustomAuthenticationForm(AuthenticationForm):
    """
    Form de login do usuário
    """
    email = forms.CharField(
        label='Endereço de E-mail',
        max_length=50,
        required=True
    )

    class Meta(AuthenticationForm):
        model = CustomUser
        fields = ('email', 'password', )
        exclude = ('username')


class CustomUserCreationForm(UserCreationForm):
    """
    Form de registro do usuário
    """
    first_name = forms.CharField(
        label="Nome",
        max_length=30,
        required=True
    )

    last_name = forms.CharField(
        label="Sobrenome",
        max_length=30,
        required=True
    )

    email = forms.CharField(
        label='Endereço de E-mail',
        max_length=50,
        required=True
    )

    class Meta(UserCreationForm):
        model = CustomUser
        fields = ('email', 'first_name', 'last_name', 'perfil')

    def __init__(self, *args, **kwargs):
        """
        Customiza as opções de perfil do usuário no registro
        """
        perfil = kwargs.pop('perfil', False)
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        if perfil:
            self.fields['perfil'].choices = perfil


class CustomUserChangeForm(UserChangeForm):
    """
    Form de alteração das informações cadastrais de um usuário
    """
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
