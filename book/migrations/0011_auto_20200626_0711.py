# Generated by Django 3.0.5 on 2020-06-26 07:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0010_auto_20200625_0913'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='title',
            field=models.CharField(default=None, max_length=60),
        ),
    ]
