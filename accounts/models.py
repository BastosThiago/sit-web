from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    ALUNO = 1
    INSTRUTOR = 2
    PERFIS = (
        (ALUNO, 'Aluno'),
        (INSTRUTOR, 'Instrutor')
    )
    perfil = models.PositiveSmallIntegerField(
        choices=PERFIS,
        null=True,
        blank=True
    )

    def __str__(self):
        return self.email

    def tem_perfil_aluno(self):
        if self.perfil == self.ALUNO:
            return True
        return False

    def tem_perfil_instrutor(self):
        if self.perfil == self.INSTRUTOR:
            return True
        return False

    def tem_perfil_administrador(self):
        return self.is_staff

