# Generated by Django 4.0.6 on 2022-07-26 10:39

import agregator.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Files',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload', models.FileField(upload_to=agregator.models.user_directory_path)),
            ],
        ),
    ]
