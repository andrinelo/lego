# -*- coding: utf-8 -*-
# Generated by Django 1.10 on 2016-11-19 15:31
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('flatpages', '0004_auto_20161018_2016'),
        ('events', '0011_registration_status'),
        ('articles', '0002_auto_20160905_2251'),
        ('comments', '0005_auto_20160905_2251'),
        ('users', '0007_auto_20161118_1731'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='interestgroup',
            name='abakusgroup_ptr',
        ),
        migrations.DeleteModel(
            name='InterestGroup',
        ),
    ]