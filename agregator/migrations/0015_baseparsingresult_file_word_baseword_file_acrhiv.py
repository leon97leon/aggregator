# Generated by Django 4.0.6 on 2022-08-05 12:37

import agregator.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agregator', '0014_baseparsingresult_sites'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseparsingresult',
            name='file_word',
            field=models.FileField(default=None, upload_to=agregator.models.user_directory_path),
        ),
        migrations.AddField(
            model_name='baseword',
            name='file_acrhiv',
            field=models.FileField(default=None, upload_to=agregator.models.user_directory_path),
        ),
    ]
