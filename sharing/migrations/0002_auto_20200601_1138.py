# Generated by Django 3.0.5 on 2020-06-01 11:38

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sharing', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookexchange',
            name='request_email',
            field=models.EmailField(blank=True, max_length=75),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='request_message',
            field=models.CharField(blank=True, max_length=200),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='request_phone_number',
            field=models.CharField(blank=True, max_length=17, validators=[django.core.validators.RegexValidator(message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.", regex='^\\+?1?\\d{9,15}$')]),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='response_meeting_address',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='response_meeting_day',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='response_meeting_hour',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='response_meeting_minute',
            field=models.CharField(blank=True, max_length=2),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='response_meeting_month',
            field=models.CharField(blank=True, max_length=10),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='response_meeting_year',
            field=models.CharField(blank=True, max_length=4),
        ),
        migrations.AddField(
            model_name='bookexchange',
            name='response_message',
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
