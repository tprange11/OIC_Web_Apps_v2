# Generated by Django 2.2.1 on 2020-02-22 22:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('thane_storck', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='skatedate',
            options={'ordering': ['skate_date']},
        ),
    ]
