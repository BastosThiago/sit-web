from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Classe de customização de um usuário padrão do Django. O objetivo aqui
    é disponibilizar o atributo de "perfil" a um usuário e também utilizar o
    e-mail do mesmo para auntenticação no sistema
    """
    ALUNO = 1
    INSTRUTOR = 2
    ADMINISTRADOR = 3
    PERFIS = (
        (ALUNO, 'Aluno'),
        (INSTRUTOR, 'Instrutor'),
        (ADMINISTRADOR, 'Administrador'),
    )

    email = models.EmailField(unique=True)

    username = models.CharField(
        max_length=150,
        null=True,
        blank=True,
    )

    perfil = models.PositiveSmallIntegerField(
        choices=PERFIS,
        null=True,
        blank=True
    )

    REQUIRED_FIELDS = []
    USERNAME_FIELD = 'email'

    def __str__(self):
        return self.email

    def tem_perfil_aluno(self):
        """
        Retorna verdadeiro se o usuário for de perfil ALUNO
        """
        if self.perfil == self.ALUNO:
            return True
        return False

    def tem_perfil_instrutor(self):
        """
        Retorna verdadeiro se o usuário for de perfil INSTRUTOR
        """
        if self.perfil == self.INSTRUTOR:
            return True
        return False

    def tem_perfil_administrador(self):
        """
        Retorna verdadeiro se o usuário for de perfil ADMINISTRADOR
        """
        if self.perfil == self.ADMINISTRADOR or self.is_staff:
            return True
        return False
