# Generated by Django 2.2.1 on 2020-07-06 15:55

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0016_auto_20200624_1349'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='WomensHockeySkateDate',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('skate_date', models.DateField()),
                ('start_time', models.CharField(max_length=10)),
                ('end_time', models.CharField(max_length=10)),
            ],
            options={
                'ordering': ['skate_date'],
                'unique_together': {('skate_date', 'start_time', 'end_time')},
            },
        ),
        migrations.CreateModel(
            name='WomensHockeySkateSession',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('goalie', models.BooleanField(default=False)),
                ('paid', models.BooleanField(default=False)),
                ('skate_date', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='session_skaters', to='womens_hockey.WomensHockeySkateDate')),
                ('skater', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.ChildSkater')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-skate_date'],
                'unique_together': {('user', 'skater', 'skate_date')},
            },
        ),
    ]