# Generated by Django 4.0.6 on 2022-08-03 11:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('agregator', '0013_alter_baseparsingresult_task_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseparsingresult',
            name='sites',
            field=models.TextField(blank=True, null=True),
        ),
    ]
