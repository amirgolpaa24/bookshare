from django.db import IntegrityError
from django.test import Client, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone
from PIL import Image
from rest_framework import status
from rest_framework.test import APIClient, APITestCase, APITransactionTestCase

from account.models import User
from book.models import Author, Book


class SearchBookAPITestCase(APITestCase):

    urls = ['book.api.urls', 'search.api.urls']

    def setUp(self):
        self.test_owner = User.objects.create(username="testowner", email="owner@alaki.com")
        self.test_searcher = User.objects.create(username="testsearcher", email="searcher@alaki.com")
        
        self.ratings_list = [1.1, 4.0, 1.9, 4.5]

        self.test_books_list = [
            {
                'title': 'The Lord of the Rings',
                'description': "The Lord of the Rings is an epic high-fantasy novel written by English author and scholar J. R. R. Tolkien. The story began as a sequel to Tolkien's 1937 fantasy novel The Hobbit, but eventually developed into a much larger work.",
                'page_num': 1000,
                'category_1': '1',
                'authors': ["J. R. R. Tolkien"],
                'publisher': "Bloomsbury",
            },
            {
                'title': 'The Master and Margarita',
                'description': "The Master and Margarita is a novel by Russian writer Mikhail Bulgakov, written in the Soviet Union between 1928 and 1940 during Stalin's regime. A censored version was published in Moscow magazine in 1966–1967, after the writer's death. The manuscript was not published as a book until 1967, in Paris.",
                'page_num': 2000,
                'category_1': '2',
                'authors': ["Mikhail Bulgakov"],
                'publisher': "Bloomsbury",
            },
            {
                'title': 'The Hobbit',
                'description': "The Hobbit, or There and Back Again is a children's fantasy novel by English author J. R. R. Tolkien. It was published on 21 September 1937 to wide critical acclaim, being nominated for the Carnegie Medal and awarded a prize from the New York Herald Tribune for best juvenile fiction.",
                'page_num': 3000,
                'category_1': '3',
                'authors': ["Tolkien"],
                'publisher': "Bloomsbury",
            },
            {
                'title': 'Harry Potter',
                'description': "Harry Potter and the Deathly Hallows is a fantasy novel written by British author J. K. Rowling and the seventh and final novel of the Harry Potter series. It was released on 21 July 2007 in the United Kingdom by Bloomsbury Publishing, in the United States by Scholastic, and in Canada by Raincoast Books.",
                'page_num': 4000,
                'category_1': '4',
                'authors': ["J. K. Rowling"],
                'publisher': "Bloomsbury",
            }
        ]

        self.owner_client = APIClient()
        self.owner_client.force_authenticate(self.test_owner)
        for test_book_data in self.test_books_list:
            response = self.owner_client.post(
                reverse('book_api:add_book'),
                data=test_book_data,
                format='json'
            )

        return super().setUp()


    def test_search_book_check_rating_effect(self):
        # adding rating and 'django' (in title) to books:
        for i, book in enumerate(Book.objects.all()):
            book.rating = self.ratings_list[i]
            book.title += ' django'
            book.save()

        searcher_client = APIClient()
        searcher_client.force_authenticate(self.test_searcher)

        response = searcher_client.put(
            reverse('search_api:search_book'),
            data={ 'query': "django" },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking rating-sorted list:
        response_data = response.data
        for i in range(len(response_data) - 1):
            self.assertGreaterEqual(response_data[i]["rating"], response_data[i + 1]["rating"])

    def test_search_book_check_title_only(self):
        # adding 'django' (in title) differently to books:
        num_djangos = [1, 4, 2, 3]
        for i, book in enumerate(Book.objects.all()):
            book.title += num_djangos[i] * ' django'
            book.save()

        searcher_client = APIClient()
        searcher_client.force_authenticate(self.test_searcher)

        response = searcher_client.put(
            reverse('search_api:search_book'),
            data={ 'query': "django" },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking rating-sorted list:
        response_data = response.data
        for i in range(len(response_data) - 1):
            self.assertGreaterEqual(response_data[i]["title"].count("django"), response_data[i + 1]["title"].count("django"))

    def test_search_book_check_description_only(self):
        # adding 'django' (in description) differently to books:
        num_djangos = [1, 4, 2, 3]
        for i, book in enumerate(Book.objects.all()):
            book.description += num_djangos[i] * ' django'
            book.save()

        searcher_client = APIClient()
        searcher_client.force_authenticate(self.test_searcher)

        response = searcher_client.put(
            reverse('search_api:search_book'),
            data={ 'query': "django" },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking rating-sorted list:
        response_data = response.data
        for i in range(len(response_data) - 1):
            self.assertGreaterEqual(response_data[i]["description"].count("django"), response_data[i + 1]["description"].count("django"))

    def test_search_book_check_author_only(self):
        # adding 'django' (in author) differently to books:
        num_djangos = [1, 4, 2, 3]
        for i, book in enumerate(Book.objects.all()):
            book.add_author(num_djangos[i] * ' django')
            book.save()

        searcher_client = APIClient()
        searcher_client.force_authenticate(self.test_searcher)

        response = searcher_client.put(
            reverse('search_api:search_book'),
            data={ 'query': "django" },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking rating-sorted list:
        response_data = response.data
        for i in range(len(response_data) - 1):
            self.assertGreaterEqual(Book.objects.get(slug=response_data[i]["slug"]).authors_str.count("django"),
                            Book.objects.get(slug=response_data[i + 1]["slug"]).authors_str.count("django"))

    def test_search_book_check_publisher_only(self):
        # adding 'django' (in publisher) differently to books:
        num_djangos = [1, 4, 2, 3]
        for i, book in enumerate(Book.objects.all()):
            book.publisher += num_djangos[i] * ' django'
            book.save()

        searcher_client = APIClient()
        searcher_client.force_authenticate(self.test_searcher)

        response = searcher_client.put(
            reverse('search_api:search_book'),
            data={ 'query': "django" },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking rating-sorted list:
        response_data = response.data
        for i in range(len(response_data) - 1):
            self.assertGreaterEqual(response_data[i]["publisher"].count("django"), response_data[i + 1]["publisher"].count("django"))

    def test_search_book_check_weights(self):
        # adding one 'django' (in all 4 fields related) books:
        for i, book in enumerate(Book.objects.all()):
            if i % 4 == 0:
                book.title += ' django'
                book.save()
            elif i % 4 == 1:
                book.description += ' django'
                book.save()
            elif i % 4 == 2:
                book.add_author(' django')
                book.save()
            elif i % 4 == 3:
                book.publisher += ' django'
                book.save()

        searcher_client = APIClient()
        searcher_client.force_authenticate(self.test_searcher)

        response = searcher_client.put(
            reverse('search_api:search_book'),
            data={ 'query': "django" },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking rating-sorted list:
        response_data = response.data
        self.assertEqual(response_data[0]["title"].count("django"), 1)
        self.assertEqual(response_data[1]["description"].count("django"), 1)
        self.assertEqual(Book.objects.get(slug=response_data[2]["slug"]).authors_str.count("django"), 1)
        self.assertEqual(response_data[3]["publisher"].count("django"), 1)


class SearchUserAPITestCase(APITestCase):

    urls = 'search.api.urls'

    def setUp(self):
        self.test_searcher = User.objects.create(username="testsearcher", email="searcher@alaki.com")
        
        self.ratings_list = [3.1, 7.0, 5.9, 8.5]

        self.test_users_list = [
            User.objects.create(
                username = 'billgates1234',
                first_name = "Michael",
                last_name = "Gates",
                email = 'billgates1234@xxx.com'
            ),
            User.objects.create(
                username = 'jeffbezos1234',
                first_name = "John",
                last_name = "Bezos",
                email = 'jeffbezos1234@xxx.com'
            ),
            User.objects.create(
                username = 'markzuck1234',
                first_name = "Bill",
                last_name = "Zuckerberg",
                email = 'markzuck1234@xxx.com'
            ),
            User.objects.create(
                username = 'muskelon1234',
                first_name = "Michael",
                last_name = "Musk",
                email = 'muskelon1234@xxx.com'
            )
        ]

        return super().setUp()


    def test_search_user_check_rating_effect(self):
        # adding rating and changing the firstnames (to 'django') for all users:
        for i, user in enumerate(User.objects.exclude(first_name__exact="")):
            user.rating = self.ratings_list[i]
            user.first_name = 'django'
            user.save()

        searcher_client = APIClient()
        searcher_client.force_authenticate(self.test_searcher)

        response = searcher_client.put(
            reverse('search_api:search_user'),
            data={ 'query': "django" },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking rating-sorted list:
        response_data = response.data
        for i in range(len(response_data) - 1):
            self.assertGreaterEqual(response_data[i]["rating"], response_data[i + 1]["rating"])

    def test_search_user_without_rating(self):
        searcher_client = APIClient()
        searcher_client.force_authenticate(self.test_searcher)

        response = searcher_client.put(
            reverse('search_api:search_user'),
            data={ 'query': "Michael" },
            format='json'
        )
        
        if response.status_code != status.HTTP_200_OK:
            print("response json:", response.data)

        # response status code:
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # checking rating-sorted list:
        response_data = response.data
        self.assertEqual(response_data[0]["last_name"], "Gates")
        self.assertEqual(response_data[1]["last_name"], "Musk")

    