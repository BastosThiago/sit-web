# Generated by Django 2.2.4 on 2019-09-17 11:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_auto_20190914_1630'),
    ]

    operations = [
        migrations.AddField(
            model_name='inscricao',
            name='data_conclusao',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]