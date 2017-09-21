# -*- coding: utf-8 -*-
# Generated by Django 1.11.5 on 2017-09-21 19:18
from __future__ import unicode_literals

import django.db.models.deletion
from django.db import migrations

import lego.apps.files.models


class Migration(migrations.Migration):

    dependencies = [
        ('files', '0002_file_user'),
        ('users', '0003_auto_20170903_2206'),
    ]

    operations = [
        migrations.AddField(
            model_name='abakusgroup',
            name='logo',
            field=lego.apps.files.models.FileField(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='group_pictures', to='files.File'),
        ),
    ]
