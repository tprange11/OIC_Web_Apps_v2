# Generated by Django 2.2.1 on 2020-02-21 15:35

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('stickandpuck', '0007_auto_20191008_1838'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stickandpucksessions',
            name='skater',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='stickandpuck.StickAndPuckSkaters'),
        ),
    ]
