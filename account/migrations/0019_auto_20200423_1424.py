# Generated by Django 3.0.5 on 2020-04-23 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0018_auto_20200423_1412'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='image',
            field=models.ImageField(default='./profile_images/default_user_profile_image.png', upload_to='profile_images/'),
        ),
    ]
