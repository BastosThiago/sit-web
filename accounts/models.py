from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    ALUNO = 1
    PROFESSOR = 2
    PERFIS = (
        (ALUNO, 'Aluno'),
        (PROFESSOR, 'Professor'),
    )
    perfil = models.PositiveSmallIntegerField(choices=PERFIS)

    def __str__(self):
        return self.email


