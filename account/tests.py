import json

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from book.models import Book
from account.models import User


class GetAccountPropertiesAPITestCase(APITestCase):

    def setUp(self):
        self.first_book_json = {
            'title': 'Test Book 1',
            'description': "Tes desciption 1",
            'page_num': 120,
            'category_1': '0',
            'authors': ["test_author1", "test_author2"],
            'edition': 6,
            'publisher': 'test_publisher1',
            'pub_year': 1995,
            'category_2': '24',
            'category_3': '30',
        }

        self.second_book_json = {
            'title': 'Test Book 2',
            'description': "Tes desciption 2",
            'page_num': 240,
            'category_1': '1',
            'authors': ["test_author3", "test_author4"],
            'edition': 7,
            'publisher': 'test_publisher2',
            'pub_year': 2005,
            'category_2': '25',
            'category_3': '31',
        }

    def test_get_book_list(self):
        owner = User.objects.create_superuser(
            username="test_owner", 
            email="test_email1@gmail.com", 
            first_name='Amir', 
            last_name='Golpayrgani', 
            password="password"
        )
        client = APIClient()
        client.force_authenticate(owner)
        
        # posting 1st book:
        first_book_json = self.first_book_json
        client.post(
            reverse('book_api:add_book'),
            data=first_book_json,
            format='json'
        )
        book1 = Book.objects.filter(title='Test Book 1')[0]
        book1_slug = book1.slug

        # posting 2nd book:
        second_book_json = self.second_book_json
        client.post(
            reverse('book_api:add_book'),
            data=second_book_json,
            format='json'
        )
        book2 = Book.objects.filter(title='Test Book 2')[0]
        book2_slug = book2.slug

        # getting account properties:
        response = client.get(
            reverse('account_api:account_properties', kwargs={'username': owner.username}),
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # books_count field:
        self.assertEqual(response.data['books_count'], 2)
        # books_list field:
        self.assertEqual(set(response.data['books_list']), set([book1_slug, book2_slug]))
        
