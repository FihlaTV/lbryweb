# Generated by Django 2.1.3 on 2018-12-14 15:35

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Operation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('started', models.DateTimeField(auto_now_add=True)),
                ('ended', models.DateTimeField(blank=True, null=True)),
                ('duration', models.FloatField(blank=True, null=True)),
                ('name', models.CharField(max_length=200)),
                ('errored', models.BooleanField(default=False)),
                ('meta', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
            ],
        ),
    ]