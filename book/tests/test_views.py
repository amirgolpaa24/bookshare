from django.db import IntegrityError
from django.test import Client, TestCase, TransactionTestCase
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APITransactionTestCase

from bookshare.settings import DEFAULT_BOOK_IMAGE, MEDIA_ROOT

from account.models import User
from book.models import Author, Book
from PIL import Image
import tempfile
import json
import os


class AddBookAPITestCase(APITestCase):

    urls = 'book.api.urls'

    def setUp(self):
        self.minimal_valid_book_json = {
            'title': 'Test Book',
            'description': "This is a test description for this test book.",
            'page_num': 120,
            'category_1': '12',
            'authors': ["test_author1", "test_author2"],
        }

        self.maximal_valid_book_json = {
            'title': 'Test Book',
            'description': "This is a test description for this test book.",
            'page_num': 120,
            'category_1': '0',
            'authors': ["test_author1", "test_author2"],
            # extra fields:
            'edition': 6,
            'publisher': 'test_publisher',
            'pub_year': 1995,
            'category_2': '24',
            'category_3': '31',
        }

        self.invalid_title_list = []

        return super().setUp()

    def test_post_minimal_valid_book(self):
        owner = User.objects.create(username="test_owner")
        client = APIClient()
        client.force_authenticate(owner)

        book_json = self.minimal_valid_book_json
        response = client.post(
            reverse('book_api:add_book'),
            data=book_json,
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book fields:
        self.assertEqual(len(Book.objects.all()), 1)
        new_book = Book.objects.all()[0]

        # checking owner of the book:
        self.assertEqual(new_book.owner, owner)

        for field in book_json:
            if field == 'authors':
                continue
            self.assertEqual(getattr(new_book, field), book_json[field])
        
        # checking authors:
        self.assertEqual(len(Author.objects.all()), len(book_json['authors']))
        for i, author_name in enumerate(book_json['authors']):
            self.assertEqual(Author.objects.all()[i].name, author_name)
            self.assertEqual(Author.objects.all()[i].book, new_book)

    def test_post_maximal_valid_book(self):
        owner = User.objects.create(username="test_owner")
        client = APIClient()
        client.force_authenticate(owner)

        book_json = self.maximal_valid_book_json
        response = client.post(
            reverse('book_api:add_book'),
            data=book_json,
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book fields:
        self.assertEqual(len(Book.objects.all()), 1)
        new_book = Book.objects.all()[0]
        for field in book_json:
            if field == 'authors':
                continue
            self.assertEqual(getattr(new_book, field), book_json[field])
        
        # checking authors:
        self.assertEqual(len(Author.objects.all()), len(book_json['authors']))
        for i, author_name in enumerate(book_json['authors']):
            self.assertEqual(Author.objects.all()[i].name, author_name)
            self.assertEqual(Author.objects.all()[i].book, new_book)
        
    def test_post_invalid_book_without_required_fields(self):
        owner = User.objects.create(username="test_owner")
        client = APIClient()
        client.force_authenticate(owner)

        invalid_book_jsons_list = [self.minimal_valid_book_json.copy() for field in self.minimal_valid_book_json]
        for invalid_book_json, field in zip(invalid_book_jsons_list, self.minimal_valid_book_json):
            invalid_book_json.pop(field)

            response = client.post(
                reverse('book_api:add_book'),
                data=invalid_book_json,
                format='json'
            )
        
            if response.status_code != status.HTTP_400_BAD_REQUEST:
                print("response json:", response.data)

            # response status code:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)        
            # checking book fields:
            self.assertEqual(len(Book.objects.all()), 0)


class EditBookAPITestCase(APITestCase):

    urls = 'book.api.urls'

    def setUp(self):
        self.initial_book_json = {
            'title': 'Test Book',
            'description': "This is a test description for this test book.",
            'page_num': 120,
            'category_1': '0',
            'authors': ["test_author1", "test_author2"],
            'edition': 6,
            'publisher': 'test_publisher',
            'pub_year': 1995,
            'category_2': '24',
            'category_3': '31',
        }

        self.valid_fully_edited_book_json = {
            'title': 'Edited Test Book',
            'description': "Edited This is a test description for this test book.",
            'page_num': 121,
            'category_1': '1',
            'edition': 7,
            'publisher': 'edited_test_publisher',
            'pub_year': 1996,
            'category_2': '25',
            'category_3': '30',
        }

        self.invalid_book_json = {
            'title': 'a' * 61,
            'description': 'a' * 401,
            'page_num': 'aaa',
            'category_1': 'aaa',
            'edition': 'aaa',
            'publisher': 'a' * 51,
            'pub_year': 'aaa',
            'category_2': 'aaa',
            'category_3': 'aaa',
        }

        self.editable_fields = list(self.valid_fully_edited_book_json.keys())

        return super().setUp()

    def test_edit_book_fully_validly(self):
        owner = User.objects.create(username="test_owner")
        client = APIClient()
        client.force_authenticate(owner)

        initial_book_json = self.initial_book_json
        client.post(
            reverse('book_api:add_book'),
            data=initial_book_json,
            format='json'
        )
        book_slug = Book.objects.all()[0].slug

        edited_book_json = self.valid_fully_edited_book_json
        client.force_authenticate(owner)
        response = client.put(
            reverse('book_api:edit_book', kwargs={'book_slug': book_slug}),
            data=edited_book_json,
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking book fields:
        self.assertEqual(len(Book.objects.all()), 1)
        book = Book.objects.all()[0]
        for field in edited_book_json:
            self.assertEqual(getattr(book, field), edited_book_json[field])
        
        # checking owner of the book:
        self.assertEqual(book.owner, owner)

        # checking authors:
        self.assertEqual(len(Author.objects.all()), len(initial_book_json['authors']))
        for i, author_name in enumerate(initial_book_json['authors']):
            self.assertEqual(Author.objects.all()[i].name, author_name)
            self.assertEqual(Author.objects.all()[i].book, book)

    def test_edit_book_partially_validly(self):
        owner = User.objects.create(username="test_owner")
        client = APIClient()
        client.force_authenticate(owner)

        initial_book_json = self.initial_book_json
        client.post(
            reverse('book_api:add_book'),
            data=initial_book_json,
            format='json'
        )
        book_slug = Book.objects.all()[0].slug

        for field in self.editable_fields:
            edited_book_json = {field: initial_book_json[field]}
            client.force_authenticate(owner)
            response = client.put(
                reverse('book_api:edit_book', kwargs={'book_slug': book_slug}),
                data=edited_book_json,
                format='json'
            )
            
            if response.status_code != status.HTTP_200_OK:
                print("response json:", response.data)

            # response status code:
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # checking book fields:
            self.assertEqual(len(Book.objects.all()), 1)
            book = Book.objects.all()[0]
            self.assertEqual(getattr(book, field), edited_book_json[field])

            for other_field in self.editable_fields:
                if other_field == field:
                    continue
                self.assertEqual(getattr(book, other_field), initial_book_json[other_field])
            
            # checking owner of the book:
            self.assertEqual(book.owner, owner)

            # checking authors:
            self.assertEqual(len(Author.objects.all()), len(initial_book_json['authors']))
            for i, author_name in enumerate(initial_book_json['authors']):
                self.assertEqual(Author.objects.all()[i].name, author_name)
                self.assertEqual(Author.objects.all()[i].book, book)

    def test_edit_book_partially_invalidly(self):
        owner = User.objects.create(username="test_owner")
        client = APIClient()
        client.force_authenticate(owner)

        initial_book_json = self.initial_book_json
        client.post(
            reverse('book_api:add_book'),
            data=initial_book_json,
            format='json'
        )
        book_slug = Book.objects.all()[0].slug

        for field in self.editable_fields:
            edited_book_json = {field: self.invalid_book_json[field]}
            client.force_authenticate(owner)
            response = client.put(
                reverse('book_api:edit_book', kwargs={'book_slug': book_slug}),
                data=edited_book_json,
                format='json'
            )
            
            if response.status_code != status.HTTP_400_BAD_REQUEST:
                print("response json:", response.data)

            # response status code:
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            
            # checking book fields:
            self.assertEqual(len(Book.objects.all()), 1)
            book = Book.objects.all()[0]
            for other_field in self.editable_fields:
                self.assertEqual(getattr(book, other_field), initial_book_json[other_field])
            
            # checking owner of the book:
            self.assertEqual(book.owner, owner)

            # checking authors:
            self.assertEqual(len(Author.objects.all()), len(initial_book_json['authors']))
            for i, author_name in enumerate(initial_book_json['authors']):
                self.assertEqual(Author.objects.all()[i].name, author_name)
                self.assertEqual(Author.objects.all()[i].book, book)

    
class DeleteBookAPITransactionTestCase(APITransactionTestCase):

    urls = 'book.api.urls'

    def setUp(self):
        self.initial_book_json = {
            'title': 'Test Book',
            'description': "This is a test description for this test book.",
            'page_num': 120,
            'category_1': '0',
            'authors': ["test_author1", "test_author2"],
            'edition': 6,
            'publisher': 'test_publisher',
            'pub_year': 1995,
            'category_2': '24',
            'category_3': '31',
        }

        return super().setUp()

    def test_delete_others_book(self):
        owner = User.objects.create(username="test_owner", email="test_email1@gmail.com")
        client1 = APIClient()
        client1.force_authenticate(owner)

        initial_book_json = self.initial_book_json
        client1.post(
            reverse('book_api:add_book'),
            data=initial_book_json,
            format='json'
        )
        book_slug = Book.objects.all()[0].slug

        # another client:
        other_user = User.objects.create(username="test_other_user", email="test_email2@gmail.com")
        client2 = APIClient()
        client2.force_authenticate(other_user)
        response = client2.delete(
            reverse('book_api:delete_book', kwargs={'book_slug': book_slug}),
        )
        
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # checking book existence:
        self.assertEqual(len(Book.objects.all()), 1)

    def test_delete_book_successfully(self):
        owner = User.objects.create(username="test_owner")
        client = APIClient()
        client.force_authenticate(owner)

        initial_book_json = self.initial_book_json
        book_slugs = []
        # adding 2 books:
        for i in range(2):
            client.post(
                reverse('book_api:add_book'),
                data=initial_book_json,
                format='json'
            )
            book_slugs.append(Book.objects.all()[i].slug)

        client.force_authenticate(owner)
        response = client.delete(
            reverse('book_api:delete_book', kwargs={'book_slug': book_slugs[0]}),
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # checking book existence:
        self.assertEqual(len(Book.objects.all()), 1)
        self.assertEqual(Book.objects.all()[0].slug, book_slugs[1])
        
    def test_delete_nonexistent_book(self):
        owner = User.objects.create(username="test_owner")
        client = APIClient()
        client.force_authenticate(owner)

        initial_book_json = self.initial_book_json
        client.post(
            reverse('book_api:add_book'),
            data=initial_book_json,
            format='json'
        )
        book_slug = Book.objects.all()[0].slug
        wrong_book_slug = book_slug[1:]

        client.force_authenticate(owner)
        response = client.delete(
            reverse('book_api:delete_book', kwargs={'book_slug': wrong_book_slug}),
        )
        
        if response.status_code != status.HTTP_400_BAD_REQUEST:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # checking book existence:
        self.assertEqual(len(Book.objects.all()), 1)


class GetBookPropertiesAPITestCase(APITestCase):

    urls = 'book.api.urls'

    def setUp(self):
        self.initial_book_json = {
            'title': 'First Test Book',
            'description': "First test description",
            'page_num': 120,
            'category_1': '0',
            'authors': ["test_author1", "test_author2"],
            'edition': 6,
            'publisher': 'first_test_publisher',
            'pub_year': 1995,
            'category_2': '24',
            'category_3': '30',
        }

        return super().setUp()

    def test_get_others_book_successfully(self):
        owner = User.objects.create(username="test_owner", email="test_email1@gmail.com", first_name='Amir', last_name='Golpayrgani')
        client1 = APIClient()
        client1.force_authenticate(owner)

        initial_book_json = self.initial_book_json
        client1.post(
            reverse('book_api:add_book'),
            data=initial_book_json,
            format='json'
        )
        book = Book.objects.all()[0]
        book_slug = book.slug

        # another client - getting owner's book:
        other_user = User.objects.create(username="test_other_user", email="test_email2@gmail.com")
        client2 = APIClient()
        client2.force_authenticate(other_user)
        response = client2.get(
            reverse('book_api:get_book_properties', kwargs={'book_slug': book_slug}),
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # checking book fields:
        for field in response.data:
            if not(response.data[field]) or field == 'authors_list' \
                                         or field == 'categories_list' \
                                         or field == 'owner_name' \
                                         or field == 'when_added':
                continue
            self.assertTrue(field in initial_book_json)
            self.assertEqual(initial_book_json[field], response.data[field])
        
        # owner_name field:
        self.assertEqual(response.data['owner_name'], owner.first_name + ' ' + owner.last_name)

        # authors_list field:
        self.assertEqual(len(response.data['authors_list']), len(initial_book_json['authors']))
        self.assertEqual(set(response.data['authors_list']), set(initial_book_json['authors']))
        
        # categories_list field:
        not_null_sent_categories = [initial_book_json[cat_field] for cat_field in initial_book_json if cat_field.startswith('category_')]
        self.assertEqual(len(response.data['categories_list']), len(not_null_sent_categories))
        self.assertEqual(set(response.data['categories_list']), set(not_null_sent_categories))

    def test_get_your_book_successfully(self):
        owner = User.objects.create(username="test_owner", email="test_email1@gmail.com")
        client = APIClient()
        client.force_authenticate(owner)

        initial_book_json = self.initial_book_json
        client.post(
            reverse('book_api:add_book'),
            data=initial_book_json,
            format='json'
        )
        book = Book.objects.all()[0]
        book_slug = book.slug

        # the owner - getting his/her own book:
        response = client.get(
            reverse('book_api:get_book_properties', kwargs={'book_slug': book_slug}),
        )

        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # checking book fields:
        for field in response.data:
            self.assertEqual(getattr(book, field), response.data[field])


class BookImageAPITestCase(APITestCase):
    
    urls = 'book.api.urls'

    def setUp(self):
        self.book_json = {
            'title': 'Test Book',
            'description': "test description",
            'page_num': 120,
            'category_1': 0,
            'authors': ["test_author1", "test_author2"],
            'edition': 6,
            'publisher': 'test_publisher',
            'pub_year': 1995,
            'category_2': 24,
            'category_3': 30,
        }

        self.image = Image.new('RGB', (100, 100))
        self.book_image_file = tempfile.NamedTemporaryFile(suffix='.jpg')
        self.image.save(self.book_image_file)

        return super().setUp()

    def test_get_default_book_image(self):
        owner = User.objects.create(username="test_owner", email="test_email1@gmail.com", first_name='Amir', last_name='Golpayrgani')
        client = APIClient()
        client.force_authenticate(owner)

        # posting the book:
        book_json = self.book_json
        client.post(
            reverse('book_api:add_book'),
            data=book_json,
            format='json'
        )
        book = Book.objects.all()[0]
        book_slug = book.slug

        # getting book image:
        response = client.get(
            reverse('book_api:get_book_image', kwargs={'book_slug': book_slug}),
        )
        book = Book.objects.all()[0]
        book_slug = book.slug

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # checking image field:
        image_received = response.content
        with open(os.path.join(MEDIA_ROOT, DEFAULT_BOOK_IMAGE), "rb") as image_file:
            self.assertEqual(image_received, image_file.read())

    def test_edit_and_get_specific_book_image(self):
        owner = User.objects.create(username="test_owner", email="test_email1@gmail.com", first_name='Amir', last_name='Golpayrgani')
        client = APIClient()
        client.force_authenticate(owner)

        # posting the book:
        book_json = self.book_json
        client.post(
            reverse('book_api:add_book'),
            data=book_json,
            format='json'
        )
        book = Book.objects.all()[0]
        book_slug = book.slug

        # editing book's image:
        with open(self.book_image_file.name, 'rb') as f:
            edit_response = client.put(
                reverse('book_api:edit_book_image', kwargs={'book_slug': book_slug}), 
                data={'image': f}, 
                format='multipart'
            )

        # getting book image:
        get_response = client.get(
            reverse('book_api:get_book_image', kwargs={'book_slug': book_slug}),
        )
        book = Book.objects.all()[0]
        book_slug = book.slug

        # 2 responses status codes:
        self.assertEqual(edit_response.status_code, status.HTTP_200_OK)
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)

        # checking image field:
        image_received = get_response.content
        with open(self.book_image_file.name, 'rb') as f:
            self.assertEqual(image_received, f.read())






