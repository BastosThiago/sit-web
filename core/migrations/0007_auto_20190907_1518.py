# Generated by Django 2.2.4 on 2019-09-07 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_auto_20190907_1514'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arquivo',
            name='arquivo',
            field=models.FileField(upload_to='arquivos_cursos'),
        ),
    ]