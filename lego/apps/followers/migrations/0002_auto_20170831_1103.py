# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-31 11:03
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('followers', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='followcompany',
            name='deleted',
        ),
        migrations.RemoveField(
            model_name='followevent',
            name='deleted',
        ),
        migrations.RemoveField(
            model_name='followuser',
            name='deleted',
        ),
    ]