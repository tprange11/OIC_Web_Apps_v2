# Generated by Django 2.2.1 on 2020-06-24 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0014_childskater'),
    ]

    operations = [
        migrations.AlterField(
            model_name='childskater',
            name='date_of_birth',
            field=models.DateField(blank=True),
        ),
    ]
