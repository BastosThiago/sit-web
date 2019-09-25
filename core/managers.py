from .models import *


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

