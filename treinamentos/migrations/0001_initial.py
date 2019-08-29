# Generated by Django 2.2.4 on 2019-08-29 10:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import treinamentos.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Alternativa',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descricao', models.TextField()),
                ('ordem', treinamentos.fields.OrderField(blank=True)),
                ('correta', models.BooleanField()),
            ],
            options={
                'ordering': ['ordem'],
            },
        ),
        migrations.CreateModel(
            name='Categoria',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Curso',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=200, unique=True)),
                ('nome_instrutor', models.CharField(max_length=150)),
                ('palavras_chaves', models.CharField(blank=True, max_length=150, null=True)),
                ('descricao', models.TextField(blank=True, max_length=150, null=True)),
                ('publicado', models.BooleanField(default=False)),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Categoria')),
            ],
        ),
        migrations.CreateModel(
            name='Questao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enunciado', models.TextField()),
                ('ordem', treinamentos.fields.OrderField(blank=True)),
            ],
            options={
                'verbose_name': 'Questão',
                'verbose_name_plural': 'Questões',
                'ordering': ['ordem'],
            },
        ),
        migrations.CreateModel(
            name='Questionario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200, unique=True)),
                ('ordem', treinamentos.fields.OrderField(blank=True)),
            ],
            options={
                'verbose_name': 'Questionário',
                'verbose_name_plural': 'Questionários',
                'ordering': ['ordem'],
            },
        ),
        migrations.CreateModel(
            name='Unidade',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200, unique=True)),
                ('ordem', treinamentos.fields.OrderField(blank=True)),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Curso')),
            ],
            options={
                'ordering': ['ordem'],
                'unique_together': {('titulo', 'curso'), ('curso', 'ordem')},
            },
        ),
        migrations.CreateModel(
            name='Video',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200, unique=True)),
                ('url', models.URLField()),
                ('ordem', treinamentos.fields.OrderField(blank=True)),
                ('unidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Unidade')),
            ],
            options={
                'verbose_name': 'Vídeo',
                'ordering': ['ordem'],
                'unique_together': {('unidade', 'ordem'), ('titulo', 'unidade')},
            },
        ),
        migrations.CreateModel(
            name='UsuarioVideo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('acessado', models.BooleanField()),
                ('data_acesso', models.DateTimeField(auto_now=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('video', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Video')),
            ],
            options={
                'verbose_name_plural': 'Registros Usuários - Vídeos',
            },
        ),
        migrations.CreateModel(
            name='UsuarioResposta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('alternativa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Alternativa')),
                ('questao', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Questao')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Registros Usuários-Respostas',
            },
        ),
        migrations.CreateModel(
            name='UsuarioQuestionario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentual_acertos', models.DecimalField(decimal_places=1, max_digits=10)),
                ('data_execucao', models.DateTimeField(auto_now=True)),
                ('questionario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Questionario')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'Registros Usuários - Questionarios',
            },
        ),
        migrations.AddField(
            model_name='questionario',
            name='unidade',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Unidade'),
        ),
        migrations.AddField(
            model_name='questao',
            name='questionario',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Questionario'),
        ),
        migrations.AddField(
            model_name='alternativa',
            name='questao',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Questao'),
        ),
        migrations.AlterUniqueTogether(
            name='questionario',
            unique_together={('unidade', 'ordem'), ('titulo', 'unidade')},
        ),
        migrations.AlterUniqueTogether(
            name='questao',
            unique_together={('questionario', 'ordem'), ('enunciado', 'questionario')},
        ),
        migrations.CreateModel(
            name='Inscricao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('percentual_andamento', models.DecimalField(decimal_places=1, max_digits=10)),
                ('percentual_acertos', models.DecimalField(decimal_places=1, max_digits=10)),
                ('situacao', models.CharField(choices=[('EM ANDAMENTO', 'EM ANDAMENTO'), ('APROVADO', 'APROVADO'), ('REPROVADO', 'REPROVADO')], default='EM ANDAMENTO', max_length=12)),
                ('obteve_certificado', models.BooleanField()),
                ('data_inscricao', models.DateTimeField(auto_now_add=True)),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Curso')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Inscrição',
                'verbose_name_plural': 'Inscrições',
                'unique_together': {('curso', 'usuario')},
            },
        ),
        migrations.CreateModel(
            name='Avaliacao',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nota', models.IntegerField(choices=[(1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5')])),
                ('comentario', models.TextField()),
                ('data_inscricao', models.DateTimeField(auto_now_add=True)),
                ('curso', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Curso')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Avaliação',
                'verbose_name_plural': 'Avaliações',
                'unique_together': {('curso', 'usuario')},
            },
        ),
        migrations.CreateModel(
            name='Arquivo',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('titulo', models.CharField(max_length=200, unique=True)),
                ('arquivo', models.FileField(upload_to='')),
                ('ordem', treinamentos.fields.OrderField(blank=True)),
                ('unidade', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='treinamentos.Unidade')),
            ],
            options={
                'ordering': ['ordem'],
                'unique_together': {('unidade', 'ordem'), ('titulo', 'unidade')},
            },
        ),
        migrations.AlterUniqueTogether(
            name='alternativa',
            unique_together={('descricao', 'questao'), ('questao', 'ordem')},
        ),
    ]
