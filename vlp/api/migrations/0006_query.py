# Generated by Django 4.2.13 on 2024-06-29 12:38

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_prediction'),
    ]

    operations = [
        migrations.CreateModel(
            name='Query',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('keyword', models.CharField(max_length=255, unique=True)),
                ('last_processed', models.DateTimeField(blank=True, default=datetime.datetime(1, 1, 1, 0, 0), null=True)),
                ('use_counter', models.PositiveIntegerField(default=0)),
                ('quality_metric', models.DecimalField(decimal_places=4, default=0, max_digits=8)),
            ],
            options={
                'ordering': ['-last_processed', 'use_counter'],
                'unique_together': {('keyword',)},
            },
        ),
    ]
