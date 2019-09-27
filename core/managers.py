from .models import *


class InscricaoManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def usuario_inscrito_curso(self, usuario, curso):
        """
            Método para verificar se o usuário está inscrito em um dado curso
        """
        inscricao = self.filter(
            usuario=usuario,
            curso=curso,
            curso__publicado=True
        )
        if inscricao.count() == 1:
            return True
        return False


class UsuarioVideoManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_videos_assistindos_por_usuario(self, curso, usuario):
        """
            Método para obter a lista de associação entre usuários e videos
        """
        usuarios_videos = self.filter(
            usuario=usuario,
            video__unidade__curso=curso
        )
        return usuarios_videos


class UsuarioQuestionarioManager(models.Manager):
    """
        Manager associado ao modelo UsuarioQuestionario
    """

    def obtem_questionarios_respondidos_por_usuario(self, curso, usuario):
        """
            Método para obter a lista de associação entre usuários e questionários
        """
        questionarios_respondidos = self.filter(
            usuario=usuario,
            questionario__unidade__curso=curso
        )
        return questionarios_respondidos

