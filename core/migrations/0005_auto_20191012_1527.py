# Generated by Django 2.2.4 on 2019-10-12 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_auto_20191012_1427'),
    ]

    operations = [
        migrations.AlterField(
            model_name='arquivo',
            name='titulo',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='questionario',
            name='titulo',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='unidade',
            name='titulo',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='video',
            name='titulo',
            field=models.CharField(max_length=200),
        ),
    ]
