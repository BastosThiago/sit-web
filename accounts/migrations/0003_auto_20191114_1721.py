# Generated by Django 2.2.4 on 2019-11-14 20:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_auto_20191111_2139'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='perfil',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(1, 'Aluno'), (2, 'Instrutor'), (3, 'Administrador')], null=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='username',
            field=models.CharField(blank=True, max_length=150, null=True),
        ),
    ]
