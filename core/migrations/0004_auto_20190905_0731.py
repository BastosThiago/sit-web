# Generated by Django 2.2.4 on 2019-09-05 10:31

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0003_auto_20190904_1834'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='curso',
            name='nome_instrutor',
        ),
        migrations.AddField(
            model_name='curso',
            name='usuario',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
