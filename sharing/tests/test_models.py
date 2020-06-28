from django.db import IntegrityError
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from datetime import timedelta

from account.models import User
from book.models import Author, Book
from sharing.models import BookExchange, calculate_duration


class BookExchangeTransactionTestCase(TransactionTestCase):

    def test_book_exchange_creation_required_fields(self):
        test_lender = User.objects.create(username="lender", email="borrower@alaki.com")
        test_book = Book.objects.create(title='test_title', description='test_description', page_num=100, category_1=0, owner=test_lender)
        test_borrower = User.objects.create(username="borrower", email="lender@alaki.com")

        with self.assertRaises(IntegrityError):
            test_book_exchange = BookExchange.objects.create()
        with self.assertRaises(IntegrityError):
            test_book_exchange = BookExchange.objects.create(book=test_book)
        with self.assertRaises(IntegrityError):
            test_book_exchange = BookExchange.objects.create(borrower=test_borrower)


class BookExchangeTestCase(TestCase):

    def setUp(self):
        self.test_lender = User.objects.create(username="lender", email="lender@alaki.com")
        self.test_book = Book.objects.create(title='test_title', description='test_description', page_num=100, category_1=0, owner=self.test_lender)
        self.test_borrower = User.objects.create(username="borrower", email="borrower@alaki.com")
        self.test_book_exchange = BookExchange.objects.create(borrower=self.test_borrower, book=self.test_book)


    def test_slug_and_state_and_str(self):
        test_book_exchange = self.test_book_exchange

        self.assertEqual(test_book_exchange.slug.split('x')[1], str(test_book_exchange.pk).split('x')[1])
        self.assertEqual(test_book_exchange.state, 0)
    
    def test_borrower_and_book_and_lender_str(self):
        test_book_exchange = self.test_book_exchange

        self.assertEqual(test_book_exchange.__str__(), test_book_exchange.book_title + " - BORROWED BY: " + test_book_exchange.borrower_username + " - FROM: " + test_book_exchange.lender_username)

    def test_calculate_duration(self):
        test_book_exchange = self.test_book_exchange
        now_time = timezone.now()

        when_1_minute = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(minutes=1))
        when_59_minutes = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(minutes=59))
        when_1_hour = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(hours=1))
        when_23_hours = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(hours=23))
        when_1_day = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(days=1))
        when_29_days = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(days=29))
        when_31_days = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(days=31))
        when_364_days = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(days=364))
        when_365_days = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(days=365))
        when_750_days = calculate_duration(test_book_exchange.date_requested, timezone.now() + timedelta(days=750))

        self.assertEqual(when_1_minute, '1 minute ago')
        self.assertEqual(when_59_minutes, '59 minutes ago')
        self.assertEqual(when_1_hour, '1 hour ago')
        self.assertEqual(when_23_hours, '23 hours ago')
        self.assertEqual(when_1_day, '1 day ago')
        self.assertEqual(when_29_days, '29 days ago')
        self.assertEqual(when_31_days, '1 month ago')
        self.assertEqual(when_364_days, '11 months ago')
        self.assertEqual(when_365_days, '1 year ago')
        self.assertEqual(when_750_days, '2 years ago')

    def test_other_custom_fields(self):
        test_book_exchange = self.test_book_exchange

        self.assertEqual(test_book_exchange.request_message, '')
        self.assertEqual(test_book_exchange.request_email, '')
        self.assertEqual(test_book_exchange.request_phone_number, '')
        self.assertEqual(test_book_exchange.response_message, '')
        self.assertEqual(test_book_exchange.response_email, '')
        self.assertEqual(test_book_exchange.response_meeting_address, '')

