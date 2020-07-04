# Generated by Django 3.0.5 on 2020-06-24 06:32

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0029_remove_user_books_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='num_borrowers',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='rating',
            field=models.FloatField(default=0.0, validators=[django.core.validators.MinValueValidator(0.0), django.core.validators.MaxValueValidator(10.0)]),
        ),
    ]