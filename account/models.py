import re

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from rest_framework.authtoken.models import Token


class UserManager(BaseUserManager):
    def create_user(self, username, first_name, last_name, email, password=None, image=None,):
        if not username:
            raise ValueError('Users must have a username')
        if not first_name:
            raise ValueError('Users must have a first name')
        if not last_name:
            raise ValueError('Users must have a last name')
        if not email:
            raise ValueError('Users must have an email address')

        user = User(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),
            image=image
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, first_name, last_name, email, password):
        user = self.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            email=self.normalize_email(email),
            password=password
        )

        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True

        user.save(using=self._db)
        return user 


def validate_persian_username(input_string=''):
    space_codepoints ='\u0020\u2000-\u200F\u2028-\u202F'
    persian_alpha_codepoints = '\u0621-\u0628\u062A-\u063A\u0641-\u0642\u0644-\u0648\u064E-\u0651\u0655\u067E\u0686\u0698\u06A9\u06AF\u06BE\u06CC'
    persian_num_codepoints = '\u06F0-\u06F9'
    punctuation_marks_codepoints = '\u060C\u061B\u061F\u0640\u066A\u066B\u066C'
    additional_arabic_characters_codepoints = '\u0629\u0643\u0649-\u064B\u064D\u06D5'
    arabic_numbers_codepoints = '\u0660-\u0669'

    return persian_alpha_codepoints + additional_arabic_characters_codepoints + punctuation_marks_codepoints + persian_num_codepoints
    # return re.search('^[\s,'+persian_alpha_codepoints+additional_arabic_characters_codepoints
    #                     +punctuation_marks_codepoints+
    #                     persian_num_codepoints+']*$', input_string)


class User(AbstractBaseUser):
    first_name =        models.CharField(max_length=30, blank=False, null=False)
    last_name =         models.CharField(max_length=40, blank=False, null=False)
    username =          models.CharField(max_length=30, unique=True, null=False, blank=False, 
                            validators=[RegexValidator('^(?=.{8,30}$)(?![_.])(?!.*[_.]{2})['\
                                + validate_persian_username() +\
                                'a-zA-Z0-9._]+(?<![_.])$', message="Username can only contain alphabets, numbers, '_', or '.' in an accepted manner;\nUsername should be 8 to 30 characters long.")])
    email =             models.EmailField(max_length=254, unique=True, blank=False, null=False)

    image =             models.ImageField(upload_to='profile_images/', default='./profile_images/default_user_profile_image.png', blank=False, null=False)
    books_count =       models.PositiveIntegerField(default=0)
    rating =            models.FloatField(default=0.0)

    date_joined =       models.DateTimeField(verbose_name='date joined', auto_now_add=True, editable=False)
    last_login =        models.DateTimeField(verbose_name='last login', auto_now=True, editable=False)

    last_retrieval =    models.DateTimeField(verbose_name='last retrieval', null=True)

    is_admin =          models.BooleanField(default=False)
    is_active =         models.BooleanField(default=False)
    is_staff =          models.BooleanField(default=False)
    is_superuser =      models.BooleanField(default=False)

    REQUIRED_FIELDS =   ['first_name', 'last_name', 'email']
    USERNAME_FIELD =    'username'
    EMAIL_FIELD =       'email'
    
    objects = UserManager()

    def has_perm(self, perm, obj=None):
        #"Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return self.is_admin

    def has_module_perms(self, app_label):
        #"Does the user have permissions to view the app `account`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def full_name(self):
        return self.first_name + ' ' + self.last_name

    def get_full_name(self):
        return self.first_name + ' ' + self.last_name
    def get_short_name(self):
        return self.first_name

    def __str__(self):
        return self.username

    class META:
        fields = ('first_name', 'last_name', 'email', 'image',)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(sender, instance=False, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)
