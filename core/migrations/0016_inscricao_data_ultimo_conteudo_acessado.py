# Generated by Django 2.2.4 on 2019-09-28 15:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_inscricao_ultimo_conteudo_acessado'),
    ]

    operations = [
        migrations.AddField(
            model_name='inscricao',
            name='data_ultimo_conteudo_acessado',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]