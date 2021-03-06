# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-05-26 00:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hello', '0002_auto_20160525_1824'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('username', models.CharField(max_length=30, primary_key=True, serialize=False)),
                ('password', models.CharField(max_length=30)),
                ('email', models.CharField(max_length=30)),
                ('phone', models.CharField(max_length=10)),
            ],
            options={
                'verbose_name_plural': 'customers',
            },
        ),
        migrations.DeleteModel(
            name='Greeting',
        ),
        migrations.RemoveField(
            model_name='subscriber',
            name='user_rec',
        ),
        migrations.DeleteModel(
            name='Subscriber',
        ),
    ]
