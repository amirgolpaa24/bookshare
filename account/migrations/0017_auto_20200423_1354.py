# Generated by Django 3.0.5 on 2020-04-23 13:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0016_auto_20200423_1345'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='books_count',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='user',
            name='rating',
            field=models.FloatField(default=0.0),
        ),
    ]
