# Generated by Django 4.0.6 on 2022-07-27 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agregator', '0003_basetask_baseparsingresult'),
    ]

    operations = [
        migrations.CreateModel(
            name='BaseWord',
            fields=[
                ('user', models.TextField()),
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('type', models.TextField()),
                ('file', models.FileField(upload_to='')),
                ('file_state', models.FileField(upload_to='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]