# Generated by Django 3.2.13 on 2022-06-28 15:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0030_profile_ament_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='open_roller_email',
            field=models.BooleanField(default=False),
        ),
    ]