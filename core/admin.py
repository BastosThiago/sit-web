from django.contrib import admin

from .models import Categoria, Curso, Inscricao, Avaliacao, \
    Unidade, Video, Arquivo, UsuarioVideo, Questionario, \
    UsuarioQuestionario, Questao, Alternativa, UsuarioResposta

# Register your models here.
admin.site.register(Categoria)
admin.site.register(Curso)
admin.site.register(Inscricao)
admin.site.register(Avaliacao)
admin.site.register(Unidade)
admin.site.register(Video)
admin.site.register(Arquivo)
admin.site.register(UsuarioVideo)
admin.site.register(Questionario)
admin.site.register(UsuarioQuestionario)
admin.site.register(Questao)
admin.site.register(Alternativa)
admin.site.register(UsuarioResposta)