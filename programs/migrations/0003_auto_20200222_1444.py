# Generated by Django 2.2.1 on 2020-02-22 20:44

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('programs', '0002_auto_20200221_1325'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='program',
            options={'ordering': ['pk']},
        ),
    ]
