# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-19 21:22
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0025_auto_20170417_1957'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='check',
            name='proccessedBy',
        ),
        migrations.RemoveField(
            model_name='check',
            name='processedOn',
        ),
        migrations.RemoveField(
            model_name='check',
            name='status',
        ),
        migrations.AlterField(
            model_name='creditcard',
            name='donation',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='myApp.Donation'),
        ),
    ]
