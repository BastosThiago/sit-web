# Generated by Django 2.2.4 on 2019-10-12 12:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20191011_1144'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='video',
            name='path',
        ),
        migrations.AddField(
            model_name='unidade',
            name='descricao',
            field=models.TextField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='video',
            name='caminho',
            field=models.FileField(blank=True, default=None, null=True, upload_to='videos'),
        ),
    ]
