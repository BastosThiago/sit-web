from django import forms

from .models import Categoria

class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria                 # modelo associado ao form
        fields = ('nome',) # campos a serem apresentados no template do form