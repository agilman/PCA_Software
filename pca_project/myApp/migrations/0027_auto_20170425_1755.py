# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2017-04-25 17:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myApp', '0026_auto_20170419_2122'),
    ]

    operations = [
        migrations.AlterField(
            model_name='donationadjustment',
            name='fee',
            field=models.FloatField(null=True),
        ),
    ]
