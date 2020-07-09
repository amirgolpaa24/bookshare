from django.db import models

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from uuid import uuid4
import os
from datetime import timedelta
from django.utils import timezone

from account.models import User


def create_book_image_upload_path(instance, filename):
    extension = filename.split('.')[-1]
    file_name = '{}.{}'.format(str(instance.pk) + '-' + uuid4().hex, extension)

    return os.path.join('book_images/', file_name)


class Book(models.Model): 
    title =             models.CharField(max_length=60, blank=False, default=None)
    description =       models.CharField(max_length=400, blank=False, default=None)
    page_num =          models.IntegerField()

    edition =           models.IntegerField(null=True)
    publisher =         models.CharField(max_length=50, blank=True)
    pub_year =          models.IntegerField(null=True)
    
    date_added =        models.DateTimeField(verbose_name='date added', default=timezone.now)

    owner =             models.ForeignKey(User, on_delete=models.CASCADE)
    slug =              models.CharField(max_length=30, unique=True)

    # book rating:
    rating =            models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    num_rates =         models.IntegerField(default=0)
    num_borrowers =     models.IntegerField(default=0)

    # There are 32 categories:
    Category_Choice =   [
                            (0, 'Novel'), (1, 'Mystery'), (2, 'Fantasy'), (3, 'Psychology'), (4, 'Journal'),
                            (5, 'Poetry'), (6, 'Education'), (7, 'Economics'), (8, 'History'), (9, 'Law'),
                            (10, 'Religious'), (11, 'Life_Style'), (12, 'Science'), (13, 'Social_Science'),
                            (14, 'Philosophy'), (15, 'Comic'), (16, 'Children'), (17, 'Art'), (18, 'Encyclopedia'),
                            (19, 'Dictionary'), (20, 'Biography'), (21, 'Horror'), (22, 'Crime'), (23, 'Tragedy'),
                            (24, 'Fairy_Tail'), (25, 'Drama'), (26, 'Fable'), (27, 'Humor'), (28, 'Young_Adult'),
                            (29, 'Play'), (30, 'Political'), (31, 'Math'),
                        ]

    category_1 =        models.CharField(max_length=30, choices=Category_Choice, blank=False, default=None)
    category_2 =        models.CharField(max_length=30, choices=Category_Choice, blank=True)
    category_3 =        models.CharField(max_length=30, choices=Category_Choice, blank=True)

    image =             models.ImageField(upload_to=create_book_image_upload_path, blank=False, null=True)
    
    authors_str =       models.CharField(max_length=250, blank=True, default="")

    @property
    def when_added(self):
        duration = timezone.now() - self.date_added
        days_passed = duration.days
        hours_passed = days_passed * 24 + duration.seconds // 3600
        
        if duration < timedelta(hours=24):
            return "{0} hours ago".format(hours_passed)
        else:
            return "{0} days ago".format(days_passed)

    @property
    def owner_name(self):
        return self.owner.full_name

    @property
    def authors_list(self):
        """ returns a list of all authors' names """

        authors_list = []
        for author in self.author_set.all():
            authors_list.append(author.name)
        return authors_list
    
    @property
    def comments_list(self):
        comments_list = self.comment_set.all()
        comments_list.sort(key=lambda obj: obj.date_written)
        return [
            {
                "text": comment.text,
                "writer": comment.writer_name,
            }
            for comment in comments_list
        ]

    @property
    def categories_list(self):
        categories_not_null = [self.category_1]
        if self.category_2:
            categories_not_null.append(self.category_2)
        if self.category_3:
            categories_not_null.append(self.category_3)
        return categories_not_null

    def generate_unique_slug(self):
        if not self.slug:
            self.slug = uuid4().hex[22:] + "@" + str(self.id)
        self.save()
        return self.slug

    def save(self, *args, **kwargs):
        self.date_added = timezone.now()

        super(Book, self).save(*args, **kwargs)

        if not(self.slug):
            self.generate_unique_slug()

    def add_author(self, author_name):
        # new_author = Author.objects.create(name=author_name, book=self)
        if self.authors_str == "":
            self.authors_str = author_name
            self.save()
        elif len(self.authors_str) + len(author_name) <= 249:
            updated_authors_str = self.authors_str + " " + author_name
            self.authors_str = updated_authors_str
            self.save()


    def __str__(self):
        return self.title + " - OWNED BY: " + self.owner_name


class Author(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    name = models.CharField(max_length=50, blank=False, default=None)

    def __str__(self):
        return self.name

