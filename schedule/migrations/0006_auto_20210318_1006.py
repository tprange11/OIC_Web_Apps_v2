# Generated by Django 2.2.1 on 2021-03-18 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedule', '0005_auto_20210216_1004'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rinkschedule',
            name='event',
            field=models.CharField(help_text="Field format for two teams: Put home team first and separate with ' vs ', a space then, lowercase vs, then a space", max_length=50),
        ),
    ]