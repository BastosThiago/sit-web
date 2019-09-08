from django import forms

from .models import *

class CategoriaForm(forms.ModelForm):

    class Meta:
        model = Categoria
        fields = ('titulo',)


class CursoForm(forms.ModelForm):

    class Meta:
        model = Curso
        fields = ('titulo', 'categoria', 'usuario',
                  'palavras_chaves', 'descricao', 'publicado',
                  )


class InscricaoForm(forms.ModelForm):

    class Meta:
        model = Inscricao
        fields = ('curso', 'usuario', 'percentual_andamento',
                  'percentual_acertos', 'situacao', 'obteve_certificado',
                  )


class AvaliacaoForm(forms.ModelForm):

    class Meta:
        model = Avaliacao
        fields = ('curso', 'usuario', 'nota',
                  'comentario',
                  )


class UnidadeForm(forms.ModelForm):

    class Meta:
        model = Unidade
        fields = ('titulo', 'curso', 'ordem',)


class VideoForm(forms.ModelForm):

    class Meta:
        model = Video
        fields = ('titulo', 'unidade', 'url', 'path', 'video_interno', 'ordem',)


class ArquivoForm(forms.ModelForm):

    class Meta:
        model = Arquivo
        fields = ('titulo', 'unidade', 'arquivo', 'ordem',)


class QuestionarioForm(forms.ModelForm):

    class Meta:
        model = Questionario
        fields = ('titulo', 'unidade', 'ordem')


class QuestaoForm(forms.ModelForm):

    class Meta:
        model = Questao
        fields = ('questionario', 'enunciado', 'ordem',)


class AlternativaForm(forms.ModelForm):

    class Meta:
        model = Alternativa
        fields = ('questao', 'descricao', 'ordem', 'correta',)