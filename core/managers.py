from .models import *


class CategoriaManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        return objetos


class AvaliacaoManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        return objetos


class CursoManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        else:
            if usuario.tem_perfil_instrutor():
                objetos = self.filter(usuario=usuario)
        return objetos


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

    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        return objetos


class UnidadeManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        else:
            if usuario.tem_perfil_instrutor():
                objetos = self.filter(curso__usuario=usuario)
        return objetos


class VideoManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        else:
            if usuario.tem_perfil_instrutor():
                objetos = self.filter(unidade__curso__usuario=usuario)
        return objetos


class ArquivoManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        else:
            if usuario.tem_perfil_instrutor():
                objetos = self.filter(unidade__curso__usuario=usuario)
        return objetos


class QuestionarioManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        else:
            if usuario.tem_perfil_instrutor():
                objetos = self.filter(unidade__curso__usuario=usuario)
        return objetos


class QuestaoManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        else:
            if usuario.tem_perfil_instrutor():
                objetos = self.filter(questionario__unidade__curso__usuario=usuario)
        return objetos


class AlternativaManager(models.Manager):
    """
        Manager associado ao modelo UsuarioVideo
    """
    def obtem_objetos_por_perfil_usuario(self, usuario):
        """
            Método para
        """
        objetos = self.none()
        if usuario.tem_perfil_administrador():
            objetos = self.all()
        else:
            if usuario.tem_perfil_instrutor():
                objetos = self.filter(questao__questionario__unidade__curso__usuario=usuario)
        return objetos


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

