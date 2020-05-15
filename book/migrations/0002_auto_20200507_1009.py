# Generated by Django 3.0.5 on 2020-05-07 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('book', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='category_1',
            field=models.CharField(choices=[('Novel', 'Novel'), ('Mystery', 'Mystery'), ('Fantasy', 'Fantasy'), ('Psychology', 'Psychology'), ('Journal', 'Journal'), ('Poetry', 'Poetry'), ('Education', 'Education'), ('Economics', 'Economics'), ('History', 'History'), ('Law', 'Law'), ('Religious', 'Religious'), ('Life_Style', 'Life Style'), ('Science', 'Science'), ('Social_Science', 'Social Science'), ('Philosophy', 'Philosophy'), ('Comic', 'Comic'), ('Children', 'Children'), ('Art', 'Art'), ('Encyclopedia', 'Encyclopedia'), ('Dictionary', 'Dictionary'), ('Biography', 'Biography'), ('Horror', 'Horror'), ('Crime', 'Crime'), ('Tragedy', 'Tragedy'), ('Fairy_Tail', 'Fairy Tail'), ('Drama', 'Drama'), ('Fable', 'Fable'), ('Humor', 'Humor'), ('Young_Adult', 'Young Adult'), ('Play', 'Play'), ('Political', 'Political'), ('Math', 'Math')], default=None, max_length=30),
        ),
        migrations.AlterField(
            model_name='book',
            name='description',
            field=models.CharField(default=None, max_length=200),
        ),
        migrations.AlterField(
            model_name='book',
            name='name',
            field=models.CharField(default=None, max_length=40),
        ),
    ]
