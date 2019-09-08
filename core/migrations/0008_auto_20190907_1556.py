# Generated by Django 2.2.4 on 2019-09-07 18:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_auto_20190907_1518'),
    ]

    operations = [
        migrations.AddField(
            model_name='video',
            name='video_interno',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='arquivo',
            name='arquivo',
            field=models.FileField(upload_to='arquivos'),
        ),
    ]
