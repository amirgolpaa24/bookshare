from django.db import IntegrityError
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APITransactionTestCase

from bookshare.settings import DEFAULT_BOOK_IMAGE, MEDIA_ROOT

from account.models import User
from book.models import Book
from sharing.models import BookExchange

from PIL import Image
import tempfile
import json
import os


class RegisterBookBorrowRequestAPITestCase(APITestCase):

    urls = 'sharing.api.urls'

    def setUp(self):
        self.test_lender = User.objects.create(username="lender", email="lender@alaki.com")
        self.test_book = Book.objects.create(title='test_title', description='test_description', page_num=100, category_1=0, owner=self.test_lender)
        self.test_borrower = User.objects.create(username="borrower", email="borrower@alaki.com")
        self.test_message = 'test request message'
        self.test_phone_number = '+989999999999'

        self.invalid_test_message = 'm' * 201                   # 201 characters
        self.invalid_test_phone_number = '+98999999999999999'   # 18 digits

        return super().setUp()


    def test_post_valid_borrow_request(self):
        client = APIClient()
        client.force_authenticate(self.test_borrower)

        response = client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book.slug}),
            data={
                'request_message': self.test_message,
                'request_phone_number': self.test_phone_number,
            },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book_exchange fields:
        book_exchange = BookExchange.objects.get(book=self.test_book.pk)

        self.assertEqual(book_exchange.book, self.test_book)
        self.assertEqual(book_exchange.borrower, self.test_borrower)
        self.assertEqual(book_exchange.lender, self.test_book.owner)

        self.assertEqual(book_exchange.request_email, self.test_borrower.email)
        self.assertEqual(book_exchange.request_message, self.test_message)
        self.assertEqual(book_exchange.request_phone_number, self.test_phone_number)
        
    def test_post_invalid_borrow_request(self):
        client = APIClient()
        client.force_authenticate(self.test_borrower)

        response = client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book.slug}),
            data={
                'request_message': self.invalid_test_message,
                'request_phone_number': self.invalid_test_phone_number,
            },
            format='json'
        )
        
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AddBookBorrowResponseAPITestCase(APITestCase):

    urls = 'sharing.api.urls'

    def setUp(self):
        self.test_lender = User.objects.create(username="lender", email="lender@alaki.com")
        self.test_book = Book.objects.create(title='test_title', description='test_description', page_num=100, category_1=0, owner=self.test_lender)
        self.test_borrower = User.objects.create(username="borrower", email="borrower@alaki.com")
        self.test_message = 'test request message'
        self.test_phone_number = '+989999999999'

        self.reject_response_data = {
            'response_result': 'reject',
        }
        self.accept_response_data = {
            'response_result': 'accept',
            'response_message': 'test response message',
            'response_meeting_address': 'test response address',
            'response_meeting_year': '1399',
            'response_meeting_month': '3',
            'response_meeting_day': '16',
            'response_meeting_hour': '19',
            'response_meeting_minute': '5',
        }
        self.meeting_time = self.accept_response_data['response_meeting_year'] + '/' +\
                            self.accept_response_data['response_meeting_month'] + '/' +\
                            self.accept_response_data['response_meeting_day'] + ' at ' +\
                            self.accept_response_data['response_meeting_hour'] + ':' +\
                            (self.accept_response_data['response_meeting_minute']).zfill(2)

        return super().setUp()


    def test_put_valid_borrow_reject_response(self):
        # sending request:
        borrower_client = APIClient()
        borrower_client.force_authenticate(self.test_borrower)

        borrower_client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book.slug}),
            data={
                'request_message': self.test_message,
                'request_phone_number': self.test_phone_number,
            },
            format='json'
        )
        
        # sending respons = reject:
        lender_client = APIClient()
        lender_client.force_authenticate(self.test_lender)
        
        response = lender_client.put(
            reverse('sharing_api:send_borrow_response', kwargs={'exchange_slug': BookExchange.objects.all()[0].slug}),
            data=self.reject_response_data,
            format='json'
        )

        book_exchange = BookExchange.objects.all()[0]

        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book_exchange fields:
        self.assertEqual(book_exchange.state, 1)

    def test_put_valid_borrow_accept_response(self):
        # sending request:
        borrower_client = APIClient()
        borrower_client.force_authenticate(self.test_borrower)

        borrower_client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book.slug}),
            data={
                'request_message': self.test_message,
                'request_phone_number': self.test_phone_number,
            },
            format='json'
        )
        
        # sending respons = accept:
        lender_client = APIClient()
        lender_client.force_authenticate(self.test_lender)

        response = lender_client.put(
            reverse('sharing_api:send_borrow_response', kwargs={'exchange_slug': BookExchange.objects.all()[0].slug}),
            data=self.accept_response_data,
            format='json'
        )

        book_exchange = BookExchange.objects.all()[0]

        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book_exchange fields:
        self.assertEqual(book_exchange.response_message, self.accept_response_data['response_message'])
        self.assertEqual(book_exchange.response_meeting_time, self.meeting_time)
        self.assertEqual(book_exchange.response_meeting_address, self.accept_response_data['response_meeting_address'])
        self.assertEqual(book_exchange.response_email, self.test_lender.email)
        self.assertEqual(book_exchange.state, 2)
       

     

class GetUserBorrowListAPITestCase(APITestCase):

    urls = 'sharing.api.urls'

    def setUp(self):
        self.test_lender1 = User.objects.create(username="lender1", email="lender1@alaki.com")
        self.test_lender2 = User.objects.create(username="lender2", email="lender2@alaki.com")
        self.test_book1 = Book.objects.create(title='test_title1', description='test_description1', page_num=100, category_1=0, owner=self.test_lender1)
        self.test_book2 = Book.objects.create(title='test_title2', description='test_description2', page_num=100, category_1=0, owner=self.test_lender1)
        self.test_book3 = Book.objects.create(title='test_title3', description='test_description3', page_num=100, category_1=0, owner=self.test_lender2)
        self.test_borrower = User.objects.create(username="borrower", email="borrower@alaki.com")

        self.test_message = 'test message'
        self.test_phone_number = '+989999999999'

        return super().setUp()


    def test_get_borrow_list_request(self):
        # sending requests:
        client = APIClient()
        client.force_authenticate(self.test_borrower)

        for test_book in [self.test_book1, self.test_book2, self.test_book3]:
            client.post(
                reverse('sharing_api:send_borrow_request', kwargs={'book_slug': test_book.slug}),
                data={
                    'request_message': self.test_message,
                    'request_phone_number': self.test_phone_number,
                },
                format='json'
            )

        # getting borrow list:
        response = client.get(
            reverse('sharing_api:get_borrow_list'),
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book_exchange fields:
        borrow_list = response.data.get('borrow_list_to_show')

        self.assertEqual(len(borrow_list), 3)
        self.assertEqual(set([borrow['lender_username'] for borrow in borrow_list]), set(['lender1', 'lender1', 'lender2']))
        self.assertEqual(set([borrow['borrower_username'] for borrow in borrow_list]), set(['borrower', 'borrower', 'borrower']))
        self.assertEqual(set([borrow['book_title'] for borrow in borrow_list]), set(['test_title1', 'test_title2', 'test_title3']))
        self.assertEqual(set([borrow['state'] for borrow in borrow_list]), set([0, 0, 0]))


class GetUserLendListAPITestCase(APITestCase):

    urls = 'sharing.api.urls'

    def setUp(self):
        self.test_lender = User.objects.create(username="lender", email="lender@alaki.com")
        self.test_book1 = Book.objects.create(title='test_title1', description='test_description1', page_num=100, category_1=0, owner=self.test_lender)
        self.test_book2 = Book.objects.create(title='test_title2', description='test_description2', page_num=100, category_1=0, owner=self.test_lender)
        self.test_book3 = Book.objects.create(title='test_title3', description='test_description3', page_num=100, category_1=0, owner=self.test_lender)
        self.test_borrower1 = User.objects.create(username="borrower1", email="borrower1@alaki.com")
        self.test_borrower2 = User.objects.create(username="borrower2", email="borrower2@alaki.com")

        self.test_message = 'test message'
        self.test_phone_number = '+989999999999'

        return super().setUp()


    def test_get_lend_list_request(self):
        # sending requests:
        borrower1_client = APIClient()
        borrower1_client.force_authenticate(self.test_borrower1)

        borrower1_client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book1.slug}),
            data={
                'request_message': self.test_message,
                'request_phone_number': self.test_phone_number,
            },
            format='json'
        )

        borrower2_client = APIClient()
        borrower2_client.force_authenticate(self.test_borrower2)

        borrower2_client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book2.slug}),
            data={
                'request_message': self.test_message,
                'request_phone_number': self.test_phone_number,
            },
            format='json'
        )
        borrower2_client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book3.slug}),
            data={
                'request_message': self.test_message,
                'request_phone_number': self.test_phone_number,
            },
            format='json'
        )

        # getting lend list:
        lender_client = APIClient()
        lender_client.force_authenticate(self.test_lender)

        response = lender_client.get(
            reverse('sharing_api:get_lend_list'),
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book_exchange fields:
        lend_list = response.data.get('lend_list_to_show')

        self.assertEqual(len(lend_list), 3)
        self.assertEqual(set([borrow['lender_username'] for borrow in lend_list]), set(['lender', 'lender', 'lender']))
        self.assertEqual(set([borrow['borrower_username'] for borrow in lend_list]), set(['borrower1', 'borrower2', 'borrower2']))
        self.assertEqual(set([borrow['book_title'] for borrow in lend_list]), set(['test_title1', 'test_title2', 'test_title3']))
        self.assertEqual(set([borrow['state'] for borrow in lend_list]), set([0, 0, 0]))

       
class GetExchangePropertiesAPITestCase(APITestCase):

    urls = 'sharing.api.urls'

    def setUp(self):
        self.test_lender = User.objects.create(username="lender", email="lender@alaki.com")
        self.test_book = Book.objects.create(title='test_title', description='test_description', page_num=100, category_1=0, owner=self.test_lender)
        self.test_borrower = User.objects.create(username="borrower", email="borrower@alaki.com")

        self.test_message = 'test message'
        self.test_phone_number = '+989999999999'

        self.reject_response_data = {
            'response_result': 'reject',
        }
        self.accept_response_data = {
            'response_result': 'accept',
            'response_message': 'test response message',
            'response_meeting_address': 'test response address',
            'response_meeting_year': '1399',
            'response_meeting_month': '3',
            'response_meeting_day': '16',
            'response_meeting_hour': '19',
            'response_meeting_minute': '5',
        }
        self.meeting_time = self.accept_response_data['response_meeting_year'] + '/' +\
                            self.accept_response_data['response_meeting_month'] + '/' +\
                            self.accept_response_data['response_meeting_day'] + ' at ' +\
                            self.accept_response_data['response_meeting_hour'] + ':' +\
                            (self.accept_response_data['response_meeting_minute']).zfill(2)

        return super().setUp()


    def test_get_borrow_request_properties(self):
        # sending requests:
        borrower_client = APIClient()
        borrower_client.force_authenticate(self.test_borrower)

        borrower_client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book.slug}),
            data={
                'request_message': self.test_message,
                'request_phone_number': self.test_phone_number,
            },
            format='json'
        )
        
        # getting borrow request properties:
        borrow_request = BookExchange.objects.all()[0]
        response = borrower_client.get(
            reverse('sharing_api:get_exchange_properties', kwargs={'exchange_slug': borrow_request.slug}),
        )

        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book_exchange fields:
        response_borrow_request = response.data

        self.assertEqual(response_borrow_request.get('state'), borrow_request.state)
        self.assertEqual(response_borrow_request.get('when_requested'), borrow_request.when_requested)
        self.assertEqual(response_borrow_request.get('when_ended'), borrow_request.when_ended)
        self.assertEqual(response_borrow_request.get('request_message'), borrow_request.request_message)
        self.assertEqual(response_borrow_request.get('request_phone_number'), borrow_request.request_phone_number)

        # checking book_exchange.book fields:
        self.assertEqual(response_borrow_request.get('book').get('title'), borrow_request.book.title)
        self.assertEqual(response_borrow_request.get('book').get('description'), borrow_request.book.description)
        self.assertEqual(response_borrow_request.get('book').get('page_num'), borrow_request.book.page_num)
        self.assertEqual(response_borrow_request.get('book').get('categories_list')[0], borrow_request.book.category_1)
       
        # checking book_exchange.lender fields:
        self.assertEqual(response_borrow_request.get('lender').get('username'), borrow_request.lender_username)
        self.assertEqual(response_borrow_request.get('lender').get('email'), borrow_request.lender.email)
        
        # checking book_exchange.lender fields:
        self.assertEqual(response_borrow_request.get('borrower').get('username'), borrow_request.borrower_username)
        self.assertEqual(response_borrow_request.get('borrower').get('email'), borrow_request.borrower.email)
       
    def test_get_borrowed_book_properties(self):
        # sending request:
        borrower_client = APIClient()
        borrower_client.force_authenticate(self.test_borrower)

        borrower_client.post(
            reverse('sharing_api:send_borrow_request', kwargs={'book_slug': self.test_book.slug}),
            data={
                'request_message': self.test_message,
                'request_phone_number': self.test_phone_number,
            },
            format='json'
        )
        
        # sending respons = reject:
        lender_client = APIClient()
        lender_client.force_authenticate(self.test_lender)
        
        lender_client.put(
            reverse('sharing_api:send_borrow_response', kwargs={'exchange_slug': BookExchange.objects.all()[0].slug}),
            data=self.accept_response_data,
            format='json'
        )

        # getting borrowed book properties:
        response = borrower_client.get(
            reverse('sharing_api:get_exchange_properties', kwargs={'exchange_slug': BookExchange.objects.all()[0].slug}),
        )
        response_data = response.data

        book_exchange = BookExchange.objects.all()[0]

        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book_exchange fields:
        self.assertEqual(response_data['book']['title'], self.test_book.title)
        self.assertEqual(response_data['book']['description'], self.test_book.description)
        self.assertEqual(response_data['lender']['username'], self.test_lender.username)
        self.assertEqual(response_data['borrower']['username'], self.test_borrower.username)
        self.assertEqual(response_data['slug'], book_exchange.slug)
        self.assertEqual(response_data['request_message'], book_exchange.request_message)
        self.assertEqual(response_data['request_phone_number'], book_exchange.request_phone_number)
        self.assertEqual(response_data['response_message'], book_exchange.response_message)
        self.assertEqual(response_data['response_meeting_address'], book_exchange.response_meeting_address)
        self.assertEqual(response_data['response_meeting_time'], book_exchange.response_meeting_time)
        self.assertEqual(response_data['state'], 2)
