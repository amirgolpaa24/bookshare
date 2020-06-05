# Generated by Django 3.0.5 on 2020-06-01 08:51

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('book', '0007_auto_20200515_1034'),
    ]

    operations = [
        migrations.CreateModel(
            name='BookExchange',
            fields=[
                ('book', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, primary_key=True, serialize=False, to='book.Book')),
                ('slug', models.CharField(max_length=30, unique=True)),
                ('state', models.IntegerField(choices=[(0, 'Requested'), (1, 'Rejected'), (2, 'Started'), (3, 'Ended'), (4, 'Overdue')], default=0)),
                ('date_requested', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date requested')),
                ('date_started', models.DateTimeField(default=None, verbose_name='date started')),
                ('date_ended', models.DateTimeField(default=None, verbose_name='date ended')),
                ('borrower', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='borrowin_book_exchanges', to=settings.AUTH_USER_MODEL)),
                ('lender', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lending_book_exchanges', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
