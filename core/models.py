from django.db import models
from django.db.models import Avg
from sistema_treinamentos.settings import AUTH_USER_MODEL
import math

from .fields import OrderField
from .managers import *


class Categoria(models.Model):
    """
        Modelo de Categorias para um curso
    """
    objects = CategoriaManager()

    titulo = models.CharField(max_length=200)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.titulo

    class CustomMeta:
        ordering_field = 'titulo'
        search_fields = ['titulo',]


class Curso(models.Model):
    """
        Modelo de Curso
    """
    objects = CursoManager()

    titulo = models.CharField(unique=True, max_length=200)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    usuario = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    palavras_chaves = models.CharField(max_length=150, null=True, blank=True)
    descricao = models.TextField(max_length=150, null=True, blank=True)
    publicado = models.BooleanField(default=False)
    data_publicado = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Curso"
        verbose_name_plural = "Cursos"

    class CustomMeta:
        ordering_field = 'titulo'
        search_fields = ['titulo', 'categoria__titulo', 'usuario__username', 'palavras_chaves', 'descricao']

    def __str__(self):
        return self.titulo

    def obtem_numero_avaliacoes(self):
        avaliacoes = Avaliacao.objects.filter(
            curso=self
        )

        return avaliacoes.count()

    def obtem_nota_media(self):
        """
            Método para obter a nota média das avaliações de um curso
        """
        nota_media_curso = 0
        avaliacoes = Avaliacao.objects.filter(
            curso=self
        )

        if avaliacoes.count() > 0:
            nota_media_curso = avaliacoes.aggregate(
                Avg('nota')
            )['nota__avg']

        #if (float(nota_media_curso) % 1) >= 0.5:
        #    nota_media_curso = math.ceil(nota_media_curso)
        #else:
        #    nota_media_curso = round(nota_media_curso)

        nota_media_curso = float("{0:.1f}".format(nota_media_curso, 1))

        return nota_media_curso

    def tem_conteudo(self):
        """
            Método que verifica se um curso tem algum conteúdo(videos, arquivos, ou questionários)
        """
        unidades = Unidade.objects.filter(curso=self)

        if unidades.count() > 0:
            videos = Video.objects.filter(unidade__in=unidades)

            if videos.count() > 0:
                return True
            else:
                arquivos = Arquivo.objects.flter(unidade__in=unidades)
                if arquivos.count() > 0:
                    return True
                else:
                    questionarios = Questionario.objects.filter(unidade__in=unidades)
                    if questionarios.count() > 0:
                        return True
                    else:
                        return False
        else:
            return False


    def obtem_unidades(self):
        """
            Método para obter todas as unidades cadastradas para um curso
        """
        unidades_curso = Unidade.objects.filter(
            curso=self
        ).order_by(
            'ordem'
        )

        return unidades_curso

    def obtem_videos(self):
        """
            Método para obter todos os vídeos cadastrados para um curso
        """
        unidades_curso = self.obtem_unidades()

        videos_curso = Video.objects.filter(
            unidade__in=unidades_curso
        )

        return videos_curso

    def obtem_arquivos(self):
        """
            Método para obter todos os arquivos cadastrados para um curso
        """
        unidades_curso = self.obtem_unidades()

        arquivos_curso = Arquivo.objects.filter(
            unidade__in=unidades_curso
        )

        return arquivos_curso

    def obtem_questionarios(self):
        """
            Método para obter todos os questionários cadastrados para um curso
        """
        unidades_curso = self.obtem_unidades()

        questionarios_curso = Questionario.objects.filter(
            unidade__in=unidades_curso
        )

        return questionarios_curso


    def obtem_percentual_andamento_por_usuario(self, usuario):
        """
            Método para obter o percentual de andamento nos conteúdos de um curso
        """
        try:
            total_videos_curso = self.obtem_videos().count()
            total_questionarios_curso = self.obtem_questionarios().count()

            total_videos_assistidos = UsuarioVideo.objects.obtem_videos_assistindos_por_usuario(
                self,
                usuario
            ).count()

            total_questionarios_respondidos = UsuarioQuestionario.objects.obtem_questionarios_respondidos_por_usuario(
                self,
                usuario
            ).count()

            total_conteudo = total_videos_curso + total_questionarios_curso
            total_conteudo_realizado = total_videos_assistidos + total_questionarios_respondidos

            percentual_andamento = (total_conteudo_realizado / total_conteudo) * 100

            return percentual_andamento
        except:
            return 0

    def obtem_percentual_acertos_por_usuario(self, usuario):
        """
            Método para obter o percentual de acertos nos questionários de um curso
        """
        try:
            questionarios_respondidos = UsuarioQuestionario.objects.obtem_questionarios_respondidos_por_usuario(
                self,
                usuario
            )

            percentual_acertos = (questionarios_respondidos.aggregate(Avg('percentual_acertos')))['percentual_acertos__avg']

            return percentual_acertos
        except:
            return 0

    def obtem_numero_inscritos(self):
        """
            Método para obter o número de inscritos no curso
        """
        numero_inscritos = Inscricao.objects.filter(curso=self).count()
        return numero_inscritos

class Inscricao(models.Model):
    """
        Modelo associado as inscrições de usuários nos cursos
    """

    objects = InscricaoManager()

    SITUACOES = [
        ('EM ANDAMENTO', 'EM ANDAMENTO'),
        ('APROVADO', 'APROVADO'),
        ('REPROVADO', 'REPROVADO'),
    ]
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    usuario = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    percentual_andamento = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    percentual_acertos = models.DecimalField(max_digits=10, decimal_places=1, default=0)
    situacao = models.CharField(max_length=12, choices=SITUACOES, default='EM ANDAMENTO')
    obteve_certificado = models.BooleanField(default=False)
    data_inscricao = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    ultimo_conteudo_acessado = models.CharField(max_length=50, null=True, blank=True)
    data_ultimo_conteudo_acessado = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Inscrição do usuário {self.usuario}"

    class Meta:
        verbose_name = "Inscrição"
        verbose_name_plural = "Inscrições"
        unique_together = (('curso', 'usuario'),)

    class CustomMeta:
        ordering_field = 'data_inscricao'
        search_fields = ['curso__titulo', 'usuario__username', 'data_inscricao']


class Avaliacao(models.Model):
    """
        Modelo associado as avaliações de um curso realizadas pelos usuários
    """
    objects = AvaliacaoManager()

    NOTAS = [
        (1, '1'),
        (2, '2'),
        (3, '3'),
        (4, '4'),
        (5, '5'),
    ]
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    usuario = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    nota = models.IntegerField(choices=NOTAS)
    comentario = models.TextField()
    data_avaliacao = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Avaliação"
        verbose_name_plural = "Avaliações"
        unique_together = (('curso', 'usuario'),)


    def __str__(self):
        return f"Avaliação do usuário {self.usuario}"

    class CustomMeta:
        ordering_field = 'data_avaliacao'
        search_fields = ['curso__titulo', 'usuario__username', 'nota', 'comentario', 'data_avaliacao']


class Unidade(models.Model):
    """
        Modelo associado as unidades de um curso
    """
    objects = UnidadeManager()

    titulo = models.CharField(max_length=200)
    curso = models.ForeignKey(Curso, on_delete=models.CASCADE)
    descricao = models.TextField(blank=True, null=True, default=None)
    ordem = OrderField(blank=True, for_fields=['curso'])

    class Meta:
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"
        ordering = ['ordem']
        unique_together = (('curso', 'ordem'),)

    def __str__(self):
        return self.titulo

    class CustomMeta:
        ordering_field = 'titulo'
        search_fields = ['titulo', 'curso__titulo']


class Video(models.Model):
    """
        Modelo associado aos vídeos de um curso
    """
    objects = VideoManager()

    titulo = models.CharField(max_length=200)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    video_interno = models.BooleanField(default=False)
    url = models.URLField(max_length=200, null=True, blank=True)
    caminho = models.FileField(upload_to='videos', null=True, blank=True, default=None)
    ordem = OrderField(blank=True, for_fields=['unidade'])

    class Meta:
        verbose_name = "Vídeo"
        verbose_name_plural = "Vídeos"
        ordering = ['ordem']
        unique_together = (('unidade', 'ordem'))

    def __str__(self):
        return self.titulo

    class CustomMeta:
        ordering_field = 'titulo'
        search_fields = ['titulo', 'unidade__titulo']


class Arquivo(models.Model):
    """
        Modelo associado aos arquivos(materiais didáticos) de um curso
    """
    objects = ArquivoManager()

    titulo = models.CharField(max_length=200)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    caminho = models.FileField(upload_to='arquivos')
    ordem = OrderField(blank=True, for_fields=['unidade'])

    class Meta:
        verbose_name = "Arquivo"
        verbose_name_plural = "Arquivos"
        ordering = ['ordem']
        unique_together = (('ordem', 'unidade'),)

    def __str__(self):
        return self.titulo

    class CustomMeta:
        ordering_field = 'titulo'
        search_fields = ['titulo', 'unidade__titulo']


class UsuarioVideo(models.Model):
    """
        Modelo associado a relação entre os usuários e videos
    """
    objects = UsuarioVideoManager()

    usuario = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    acessado = models.BooleanField(default=True)
    data_acesso = models.DateTimeField(auto_now=True)
    tempo_corrente = models.DecimalField(max_digits=10, decimal_places=0, default=0)
    assistido = models.BooleanField(default=False)
    data_assistido = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Registros Usuários - Vídeos"

    def __str__(self):
        return f"{self.usuario} - {self.video}"


class UsuarioArquivo(models.Model):
    """
        Modelo associado a relação entre os usuários e videos
    """
    objects = UsuarioVideoManager()

    usuario = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    arquivo = models.ForeignKey(Arquivo, on_delete=models.CASCADE)
    acessado = models.BooleanField(default=False)
    data_acesso = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Registros Usuários - Arquivos"

    def __str__(self):
        return f"{self.usuario} - {self.arquivo}"


class Questionario(models.Model):
    """
        Modelo associado aos questionários de um curso
    """
    objects = QuestionarioManager()

    titulo = models.CharField(max_length=200)
    unidade = models.ForeignKey(Unidade, on_delete=models.CASCADE)
    ordem = OrderField(blank=True, for_fields=['unidade'])

    class Meta:
        verbose_name = "Questionário"
        verbose_name_plural = "Questionários"
        ordering = ['ordem']
        unique_together = (('ordem', 'unidade'),)

    def __str__(self):
        return self.titulo

    class CustomMeta:
        ordering_field = 'titulo'
        search_fields = ['titulo', 'unidade__titulo']


class UsuarioQuestionario(models.Model):
    """
        Modelo associado a relação entre os usuários e questionários
    """
    objects = UsuarioQuestionarioManager()

    usuario = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE)
    percentual_acertos = models.DecimalField(max_digits=10, decimal_places=1)
    respondido = models.BooleanField(default=False)
    data_execucao = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Registros Usuários - Questionarios"

    def __str__(self):
        return f"{self.usuario} - {self.questionario}"


class Questao(models.Model):
    """
        Modelo associado as questões de questionários de um curso
    """
    objects = QuestaoManager()

    questionario = models.ForeignKey(Questionario, on_delete=models.CASCADE)
    enunciado = models.TextField()
    ordem = OrderField(blank=True, for_fields=['questionario'])

    class Meta:
        verbose_name = "Questão"
        verbose_name_plural = "Questões"
        ordering = ['ordem']
        unique_together = (('questionario', 'ordem'),)

    def __str__(self):
        return self.enunciado

    class CustomMeta:
        ordering_field = 'ordem'
        search_fields = ['questionario_titulo', 'enunciado']


class Alternativa(models.Model):
    """
        Modelo associado as alternativas de questões de questionários de um curso
    """
    objects = AlternativaManager()

    questao = models.ForeignKey(Questao, on_delete=models.CASCADE)
    descricao = models.TextField()
    ordem = OrderField(blank=True, for_fields=['questao'])
    correta = models.BooleanField()

    class Meta:
        verbose_name = "Alternativa"
        verbose_name_plural = "Alternativas"
        ordering = ['ordem']
        unique_together = (('questao', 'ordem'),)

    def __str__(self):
        return self.descricao

    class CustomMeta:
        ordering_field = 'ordem'
        search_fields = ['descricao', 'questao__enunciado']


class UsuarioResposta(models.Model):
    """
        Modelo associado as respostas dos usuários para as questões
    """
    usuario = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    questao = models.ForeignKey(Questao, on_delete=models.CASCADE)
    alternativa = models.ForeignKey(Alternativa, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.usuario} - {self.questao} - {self.alternativa}"

    class Meta:
        verbose_name_plural = "Registros Usuários-Respostas"