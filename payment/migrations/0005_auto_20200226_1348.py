# Generated by Django 2.2.1 on 2020-02-26 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0004_auto_20200221_0935'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='note',
            field=models.CharField(max_length=200),
        ),
    ]
