# Generated by Django 3.0.5 on 2020-06-24 13:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0008_auto_20200624_0632'),
    ]

    operations = [
        migrations.AddField(
            model_name='book',
            name='num_rates',
            field=models.IntegerField(default=0),
        ),
    ]
