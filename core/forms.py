from django import forms

from .models import *


class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ('titulo',)

    def __init__(self, user, *args, **kwargs):
        super(CategoriaForm, self).__init__(*args, **kwargs)


class CursoForm(forms.ModelForm):

    class Meta:
        model = Curso
        fields = ('titulo', 'categoria',
                  'palavras_chaves', 'descricao', 'publicado',
                  )

    def __init__(self, user, *args, **kwargs):
        super(CursoForm, self).__init__(*args, **kwargs)


class CursoAdminForm(forms.ModelForm):

    class Meta:
        model = Curso
        fields = ('titulo', 'categoria', 'nome_instrutor',
                  'palavras_chaves', 'descricao', 'publicado',
                  )

    def __init__(self, user, *args, **kwargs):
        super(CursoAdminForm, self).__init__(*args, **kwargs)


class InscricaoForm(forms.ModelForm):

    class Meta:
        model = Inscricao
        fields = ('curso', 'usuario', 'percentual_andamento',
                  'percentual_acertos', 'situacao', 'obteve_certificado',
                  )

    def __init__(self, user, *args, **kwargs):
        super(InscricaoForm, self).__init__(*args, **kwargs)


class AvaliacaoForm(forms.ModelForm):

    class Meta:
        model = Avaliacao
        fields = ('curso', 'usuario', 'nota',
                  'comentario',
                  )

    def __init__(self, user, *args, **kwargs):
        super(AvaliacaoForm, self).__init__(*args, **kwargs)


class UnidadeForm(forms.ModelForm):

    class Meta:
        model = Unidade
        fields = ('titulo', 'curso', 'ordem',)

    def __init__(self, user, *args, **kwargs):
        super(UnidadeForm, self).__init__(*args, **kwargs)
        if user != None and user.tem_perfil_instrutor():
            self.fields['curso'].queryset = Curso.objects.filter(usuario=user)


class VideoForm(forms.ModelForm):

    class Meta:
        model = Video
        fields = ('titulo', 'unidade', 'url', 'caminho', 'ordem',)

    def __init__(self, user, *args, **kwargs):
        super(VideoForm, self).__init__(*args, **kwargs)
        if user != None and user.tem_perfil_instrutor():
            self.fields['unidade'].queryset = Unidade.objects.filter(curso__usuario=user)


    def clean(self):

        # data from the form is fetched using super function
        super(VideoForm, self).clean()

        # extract the username and text field from the data
        url = self.cleaned_data.get('url')
        path = self.cleaned_data.get('caminho')

        # conditions to be met for the username length
        if (url == None or len(url) == 0) and path == None:
            #self._errors['url'] = self.error_class([
            #    'URL inválida'])
            raise forms.ValidationError('Configure uma URL ou selecione um arquivo de vídeo')

            # return any errors if found
        return self.cleaned_data


class ArquivoForm(forms.ModelForm):

    class Meta:
        model = Arquivo
        fields = ('titulo', 'unidade', 'caminho', 'ordem',)

    def __init__(self, user, *args, **kwargs):
        super(ArquivoForm, self).__init__(*args, **kwargs)
        if user != None and user.tem_perfil_instrutor():
            self.fields['unidade'].queryset = Unidade.objects.filter(curso__usuario=user)


class QuestionarioForm(forms.ModelForm):

    class Meta:
        model = Questionario
        fields = ('titulo', 'unidade', 'ordem')

    def __init__(self, user, *args, **kwargs):
        super(QuestionarioForm, self).__init__(*args, **kwargs)
        if user != None and user.tem_perfil_instrutor():
            self.fields['unidade'].queryset = Unidade.objects.filter(curso__usuario=user)


class QuestaoForm(forms.ModelForm):

    class Meta:
        model = Questao
        fields = ('questionario', 'enunciado', 'ordem',)

    def __init__(self,  user, *args, **kwargs):
        super(QuestaoForm, self).__init__(*args, **kwargs)
        if user != None and user.tem_perfil_instrutor():
            self.fields['questionario'].queryset = Questionario.objects.filter(
                unidade__curso__usuario=user
            )


class AlternativaForm(forms.ModelForm):

    class Meta:
        model = Alternativa
        fields = ('questao', 'descricao', 'ordem', 'correta',)

    def __init__(self,  user, *args, **kwargs):
        super(AlternativaForm, self).__init__(*args, **kwargs)
        if user != None and user.tem_perfil_instrutor():
            self.fields['questao'].queryset = Questao.objects.filter(
                questionario__unidade__curso__usuario=user
            )