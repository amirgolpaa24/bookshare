# Generated by Django 3.0.5 on 2020-06-27 11:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0014_auto_20200627_0718'),
    ]

    operations = [
        migrations.AlterField(
            model_name='author',
            name='book',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='book.Book'),
        ),
    ]
