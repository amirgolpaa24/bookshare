# Generated by Django 3.0.5 on 2020-06-27 07:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0013_book_authors_str'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='authors_str',
            field=models.CharField(blank=True, default='', max_length=250),
        ),
    ]