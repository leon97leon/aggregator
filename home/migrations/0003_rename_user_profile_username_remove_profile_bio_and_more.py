# Generated by Django 4.0.6 on 2022-07-22 14:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0002_profile'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='user',
            new_name='username',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='bio',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='birth_date',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='location',
        ),
        migrations.AddField(
            model_name='profile',
            name='fio',
            field=models.TextField(blank=True),
        ),
    ]
