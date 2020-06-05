from datetime import timedelta
from uuid import uuid4

from django.core.exceptions import ValidationError

from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone

# from sharing.api.serializers import BookExchangeBorrowRequestSerializer

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
    (3, 'Ended'),
    (4, 'Overdue'),
)


class BookExchange(models.Model): 
    # notice: each book can currently be in only one exchange
    book =                      models.OneToOneField(Book, on_delete=models.CASCADE, primary_key=True)
    borrower =                  models.ForeignKey(User, on_delete=models.CASCADE, related_name='borrow_exchange')
    lender =                    models.ForeignKey(User, on_delete=models.CASCADE, related_name='lend_exchange', null=True)

    slug =                      models.CharField(max_length=30, unique=True)

    state =                     models.IntegerField(choices=BOOK_EXCHANGE_STATES, default=0)

    date_requested =            models.DateTimeField(verbose_name='date requested', default=timezone.now)
    date_started =              models.DateTimeField(verbose_name='date started', default=timezone.now)
    date_ended =                models.DateTimeField(verbose_name='date ended', default=timezone.now)


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


    @property
    def response_meeting_time(self):
        return  self.response_meeting_year + '/' +\
                self.response_meeting_month + '/' +\
                self.response_meeting_day + ' at ' +\
                self.response_meeting_hour + ':' +\
                self.response_meeting_minute

    @property
    def get_lender(self):
        return self.book.lender

    @property
    def when_requested(self):
        return calculate_duration(self.date_requested, timezone.now())

    @property
    def when_started(self):
        return calculate_duration(self.date_started, timezone.now())

    @property
    def when_ended(self):
        return calculate_duration(self.date_ended, timezone.now())

    @property
    def borrower_username(self):
        return self.borrower.username

    @property
    def lender_username(self):
        return self.lender.username

    @property
    def book_title(self):
        return self.book.title


    def generate_unique_slug(self):
        if not self.slug:
            self.slug = uuid4().hex[22:] + "x" + str(self.pk)
        self.save()
        return self.slug

    def save(self, *args, **kwargs):
        super(BookExchange, self).save(*args, **kwargs)

        self.lender = self.book.owner

        if not(self.slug):
            self.generate_unique_slug()


    @property
    def is_started(self):
        return self.state == 2
    
    @property
    def is_rejected(self):
        return self.state == 1
    
    @property
    def is_ended(self):
        return self.state == 3


    # when the borrower sends a borrow request
    ### then HIS EMAIL WILL BE SEEN by the lender/owner of the book
    def request(self, request_message, phone_number):
        # it returns the result: success or not
        if self.state == 0:
            self.date_requested = timezone.now()

            self.request_email = self.borrower.email
            self.save()

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
        if self.state == 0:
            self.state = 2
            self.date_started = timezone.now()

            self.response_email = self.lender.email
            self.save()

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
        if self.state == 0:
            self.state = 1
            self.date_ended = timezone.now()

            self.save()
            
            return True
        else:
            return False
        
    # when the borrower returns the book to the lender (its owner)
    def end(self):
        # it returns the result: success or not
        if self.state == 2:
            self.state = 3
            self.date_ended = timezone.now()

            self.save()

            return True
        else:
            return False


    def __str__(self):
        return self.book_title + " - BORROWED BY: " + self.borrower_username + " - FROM: " + self.lender_username
