from datetime import timedelta
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import (MaxValueValidator, MinValueValidator,
                                    RegexValidator)
from django.db import models
from django.utils import timezone

from account.models import User
from book.models import Book


def calculate_duration(start_date, end_date):
    duration = end_date - start_date
    
    days_passed =       duration.days
    months_passed =     days_passed // 31
    years_passed =      days_passed // 365
    hours_passed =      days_passed * 24 + duration.seconds // 3600
    minutes_passed =    duration.seconds // 60
    
    if minutes_passed == 0:
        minutes_passed = 1
    
    if duration < timedelta(hours=1):
        return "{0} minute{1} ago".format(minutes_passed, 's' * (minutes_passed > 1))
    elif duration < timedelta(hours=24):
        return "{0} hour{1} ago".format(hours_passed, 's' * (hours_passed > 1))
    elif days_passed < 31:
        return "{0} day{1} ago".format(days_passed, 's' * (days_passed > 1))
    elif days_passed < 365:
        return "{0} month{1} ago".format(months_passed, 's' * (months_passed > 1))
    else:
        return "{0} year{1} ago".format(years_passed, 's' * (years_passed > 1))


phone_number_regex_validator = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")


BOOK_EXCHANGE_STATES = (
    (0, 'Requested'),
    (1, 'Rejected'),
    (2, 'Started'),
    (3, 'Delivered'),
    (4, 'Ended'),
    (5, 'Closed'),
    (6, 'Overdue'),
)


class BookExchange(models.Model): 
    # notice: each book can currently be in only one exchange
    book =                      models.ForeignKey(Book, on_delete=models.CASCADE)
    borrower =                  models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_exchange')
    lender =                    models.ForeignKey(User, on_delete=models.CASCADE, related_name='lend_exchange', null=True)
    slug =                      models.CharField(max_length=30, primary_key=True)
    state =                     models.IntegerField(choices=BOOK_EXCHANGE_STATES, default=0)

    date_requested =            models.DateTimeField(verbose_name='date requested', default=timezone.now)
    date_started =              models.DateTimeField(verbose_name='date started', default=timezone.now)
    date_delivered =            models.DateTimeField(verbose_name='date delivered', default=timezone.now)
    date_ended =                models.DateTimeField(verbose_name='date ended', default=timezone.now)
    date_closed =               models.DateTimeField(verbose_name='date closed', default=timezone.now)
    # for sorting according to the time of last change:
    date_last_changed =         models.DateTimeField(verbose_name='date last changed', default=timezone.now)

    # fields that the BORROWER sets while requesting:
    request_message =           models.CharField(max_length=200, blank=True)
    request_email =             models.EmailField(max_length=75, blank=True)
    request_phone_number =      models.CharField(validators=[phone_number_regex_validator], max_length=17, blank=True)

    # fields that the LENDER sets while responding:
    response_message =          models.CharField(max_length=200, blank=True)
    response_email =            models.EmailField(max_length=75, blank=True)
    response_meeting_address =  models.CharField(max_length=150, blank=True)
    # meeting time:
    response_meeting_year =     models.CharField(max_length=4, blank=True)
    response_meeting_month =    models.CharField(max_length=10, blank=True)
    response_meeting_day =      models.CharField(max_length=2, blank=True)
    response_meeting_hour =     models.CharField(max_length=2, blank=True)
    response_meeting_minute =   models.CharField(max_length=2, blank=True)

    # fields that the LENDER sets while delivering the book:
    return_meeting_address =    models.CharField(max_length=150, blank=True)
    # meeting time:
    return_meeting_year =       models.CharField(max_length=4, blank=True)
    return_meeting_month =      models.CharField(max_length=10, blank=True)
    return_meeting_day =        models.CharField(max_length=2, blank=True)
    return_meeting_hour =       models.CharField(max_length=2, blank=True)
    return_meeting_minute =     models.CharField(max_length=2, blank=True)

    # fields related to returning and rating:
    lender_rating =             models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])
    book_rating =               models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(5)])
    borrower_rating =           models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(10)])

    has_lender_rated =          models.BooleanField(default=False)
    has_borrower_rated =        models.BooleanField(default=False)

    @property
    def response_meeting_time(self):
        return  self.response_meeting_year + '/' +\
                self.response_meeting_month + '/' +\
                self.response_meeting_day + ' at ' +\
                self.response_meeting_hour + ':' +\
                self.response_meeting_minute
    @property
    def return_meeting_time(self):
        return  self.return_meeting_year + '/' +\
                self.return_meeting_month + '/' +\
                self.return_meeting_day + ' at ' +\
                self.return_meeting_hour + ':' +\
                self.return_meeting_minute
    @property
    def book_comment(self):
        try:
            return Comment.objects.get(book_exchange=self).text
        except Comment.DoesNotExist:
            return None

    @property
    def when_requested(self):
        return calculate_duration(self.date_requested, timezone.now())
    @property
    def when_started(self):
        return calculate_duration(self.date_started, timezone.now())
    @property
    def when_rejected(self):
        return calculate_duration(self.date_rejected, timezone.now())
    @property
    def when_delivered(self):
        return calculate_duration(self.date_delivered, timezone.now())
    @property
    def when_ended(self):
        return calculate_duration(self.date_ended, timezone.now())
    @property
    def when_closed(self):
        return calculate_duration(self.date_closed, timezone.now())
    @property
    def when_last_changed(self):
        return calculate_duration(self.date_last_changed, timezone.now())
    
    @property
    def borrower_username(self):
        return self.borrower.username
    @property
    def lender_username(self):
        return self.lender.username
    @property
    def book_title(self):
        return self.book.title

    @property
    def is_requested(self):
        return self.state == 0
    @property
    def is_rejected(self):
        return self.state == 1
    @property
    def is_started(self):
        return self.state == 2
    @property
    def is_delivered(self):
        return self.state == 3
    @property
    def is_ended(self):
        return self.state == 4


    # when the borrower sends a borrow request
    ### then HIS EMAIL WILL BE SEEN by the lender/owner of the book
    def request(self, request_message, phone_number):
        # it returns the result: success or not
        if self.state == 0:
            self.date_requested = timezone.now()
            self.sorted_date = self.date_requested
            self.request_email = self.borrower.email
            
            self.request_message = request_message
            self.request_phone_number = phone_number
            try:
                self.clean_fields()
                self.save()
            except ValidationError as ve:
                return {k:list(map(str, ve.error_dict[k][0])) for k in ve.error_dict}

            return True
        else:
            return False

    # when the lender accept & the lending period starts
    ### then HIS EMAIL WILL BE SEEN by the borrower/requester of the book
    def accept(self, response_message, meeting_address, meeting_year, meeting_month, meeting_day, meeting_hour, meeting_minute):
        # it returns the result: success or not
        if self.is_requested:
            self.state = 2
            self.date_started = timezone.now()
            self.sorted_date = self.date_started
            self.response_email = self.lender.email
            
            self.response_message = response_message
            self.response_meeting_address = meeting_address
            self.response_meeting_year = meeting_year
            self.response_meeting_month = meeting_month
            self.response_meeting_day = meeting_day
            self.response_meeting_hour = meeting_hour
            self.response_meeting_minute = meeting_minute.zfill(2)
            try:
                self.clean_fields()
                self.save()
            except ValidationError as ve:
                return {k:list(map(str, ve.error_dict[k][0])) for k in ve.error_dict}

            return True
        else:
            return False

    # when the lender rejects the request
    def reject(self):
        # it returns the result: success or not
        if self.is_requested:
            self.state = 1
            self.date_rejected = timezone.now()
            self.sorted_date = self.date_rejected

            self.save()
            
            return True
        else:
            return False
        
    # when the lender delivers the book to the borrower
    def deliver(self, meeting_address, meeting_year, meeting_month, meeting_day, meeting_hour, meeting_minute):
        # it returns the result: success or not
        if self.is_started: 
            self.state = 3
            self.date_delivered = timezone.now()
            self.sorted_date = self.date_delivered

            self.book.num_borrowers += 1
            self.lender.num_borrowers += 1
            self.borrower.num_lenders += 1

            self.return_meeting_address = meeting_address
            self.return_meeting_year = meeting_year
            self.return_meeting_month = meeting_month
            self.return_meeting_day = meeting_day
            self.return_meeting_hour = meeting_hour
            self.return_meeting_minute = meeting_minute.zfill(2)
            try:
                self.book.clean_fields(exclude=['edition', 'pub_year', 'category_1', 'image'])
                self.lender.clean_fields(exclude=['first_name', 'last_name', 'password', 'username', 'image', 'last_retrieval'])
                self.borrower.clean_fields(exclude=['first_name', 'last_name', 'password', 'username', 'image', 'last_retrieval'])
                self.clean_fields()
                self.book.save()
                self.lender.save()
                self.borrower.save()
                self.save()
            except ValidationError as ve:
                return {k:list(map(str, ve.error_dict[k][0])) for k in ve.error_dict}

            return True
        else:
            return False

    # when the borrower returns the book to the lender (its owner)
    def end(self, lender_rating: int, book_rating: int, book_comment=""):
        # it returns the result: success or not
        if self.is_delivered or self.is_ended:
            self.state += 1
            self.date_ended = timezone.now()
            self.sorted_date = self.date_ended

            self.lender_rating = lender_rating
            self.book_rating = book_rating
            self.has_borrower_rated = True

            self.lender.num_rates += 1
            self.book.num_rates += 1
            self.lender.rating = ((self.lender.rating * (self.lender.num_rates - 1)) + lender_rating) / self.lender.num_rates
            self.book.rating = ((self.book.rating * (self.book.num_rates - 1)) + book_rating) / self.book.num_rates
            if book_comment:
                new_comment = Comment(book_exchange=self, text=book_comment)
            try:
                self.clean_fields()
                self.lender.clean_fields(exclude=['first_name', 'last_name', 'password', 'username', 'image', 'last_retrieval'])
                self.book.clean_fields(exclude=['edition', 'pub_year', 'category_1', 'image'])
                if book_comment:
                    new_comment.clean_fields()

                self.save()
                self.lender.save()
                self.book.save()
                if book_comment:
                    new_comment.save()
            except ValidationError as ve:
                return {k:list(map(str, ve.error_dict[k][0])) for k in ve.error_dict}

            return True
        else:
            return False

    # when the lender rates the borrower:
    def rate_borrower(self, borrower_rating: int):
        # it returns the result: success or not
        if self.is_delivered or self.is_ended: 
            self.state += 1
            self.date_closed = timezone.now()
            self.sorted_date = self.date_closed

            self.borrower_rating = borrower_rating
            self.has_lender_rated = True

            self.borrower.num_rates += 1
            self.borrower.rating = ((self.borrower.rating * (self.borrower.num_rates - 1)) + borrower_rating) / self.borrower.num_rates
            try:
                self.borrower.clean_fields(exclude=['first_name', 'last_name', 'password', 'username', 'image', 'last_retrieval'])
                self.clean_fields()
                self.borrower.save()
                self.save()
            except ValidationError as ve:
                return {k:list(map(str, ve.error_dict[k][0])) for k in ve.error_dict}

            return True
        else:
            return False


    def generate_unique_slug(self):
        if not self.slug:
            new_slug = uuid4().hex[22:] + "x" + uuid4().hex[23:]
            while BookExchange.objects.filter(slug=new_slug).exists():
                new_slug = uuid4().hex[22:] + "x" + uuid4().hex[23:]
            self.slug = new_slug
            return new_slug

    def save(self, *args, **kwargs):
        is_first_time = not(self.slug)
        if is_first_time:
            self.generate_unique_slug()

        super(BookExchange, self).save(*args, **kwargs)

        if is_first_time:
            self.lender = self.book.owner
            self.save()

    def __str__(self):
        return self.book_title + " - BORROWED BY: " + self.borrower_username + " - FROM: " + self.lender_username


class Comment(models.Model):
    book_exchange = models.ForeignKey(BookExchange, on_delete=models.CASCADE)
    date_written =  models.DateTimeField(verbose_name='date written', default=timezone.now)

    text =          models.CharField(max_length=150)

    @property
    def writer_name():
        return self.writer.full_name

    def __str__(self):
        res = self.writer_name + ": "
        if len(self.text) > 40:
            res += self.text[:40] + "..."
        else:
            res += self.text
        return res

    def save(self, *args, **kwargs):
        self.date_written = timezone.now()
        self.book = self.book_exchange.book

        super(Comment, self).save(*args, **kwargs)
