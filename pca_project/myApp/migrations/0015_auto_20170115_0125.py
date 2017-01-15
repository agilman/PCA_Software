# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-01-15 01:25
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0014_donor_formdate'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='donor',
            name='formDate',
        ),
        migrations.AddField(
            model_name='donation',
            name='formDate',
            field=models.DateField(default=datetime.date(2017, 1, 10)),
            preserve_default=False,
        ),
    ]
