# Generated by Django 2.2.23 on 2022-01-25 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0027_profile_kranich_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='caribou_email',
            field=models.BooleanField(default=False),
        ),
    ]