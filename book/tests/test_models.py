from django.test import TestCase, TransactionTestCase
from book.models import Book, Author
from django.utils import timezone

from account.models import User
from django.db import IntegrityError


class BookTransactionTestCase(TransactionTestCase):

    def test_book_creation_required_fields(self):
        test_title = "test_title"
        test_description = "test_description"
        test_page_num = 123
        test_owner = User.objects.create(username="test_user")
        test_category_1 = Book.Category_Choice[0]

        with self.assertRaises(IntegrityError):
            test_book = Book.objects.create()
        with self.assertRaises(IntegrityError):
            test_book = Book.objects.create(description=test_description, page_num=test_page_num, owner=test_owner, category_1=test_category_1)
        with self.assertRaises(IntegrityError):
            test_book = Book.objects.create(title=test_title, page_num=test_page_num, owner=test_owner, category_1=test_category_1)
        with self.assertRaises(IntegrityError):
            test_book = Book.objects.create(title=test_title, description=test_description, owner=test_owner, category_1=test_category_1)
        with self.assertRaises(IntegrityError):
            test_book = Book.objects.create(title=test_title, description=test_description, page_num=test_page_num, category_1=test_category_1)
        with self.assertRaises(IntegrityError):
            test_book = Book.objects.create(title=test_title, description=test_description, page_num=test_page_num, owner=test_owner)


class BookTestCase(TestCase):

    def test_date_added(self):
        test_book = Book.objects.create(title = "test_title", description="test_description", page_num=666, owner=User.objects.create(username="test_user"), category_1=Book.Category_Choice[0])
        now_time = timezone.now()

        self.assertGreaterEqual(now_time, test_book.date_added)
        self.assertLessEqual(now_time, test_book.date_added + timezone.timedelta(seconds=1))

    def test_add_author(self):
        test_book = Book.objects.create(title = "test_title", description="test_description", page_num=666, owner=User.objects.create(username="test_user"), category_1=Book.Category_Choice[0])
        test_book.add_author("test_author")
        
        self.assertEquals(len(test_book.author_set.all()), 1)
        self.assertEquals(test_book.author_set.all()[0].name, "test_author")
        self.assertEquals(test_book.author_set.all()[0].book, test_book)
    
    def test_categories(self):
        test_category_1 = Book.Category_Choice[0]
        test_book = Book.objects.create(title = "test_title", description="test_description", page_num=666, owner=User.objects.create(username="test_user"), category_1=test_category_1)
        self.assertEqual(test_book.categories, [test_category_1])

        test_category_2 = Book.Category_Choice[0]
        test_book.category_2 = test_category_2
        test_book.save()
        self.assertEqual(test_book.categories, [test_category_1, test_category_2])

        test_category_3 = Book.Category_Choice[0]
        test_book.category_3 = test_category_3
        test_book.save()
        self.assertEqual(test_book.categories, [test_category_1, test_category_2, test_category_3])


class AuthorTransactionTestCase(TransactionTestCase):

    def test_author_creation_required_fields(self):
        test_name = "test_name"
        test_book = Book.objects.create(title = "test_name", description="test_description", page_num=666, owner=User.objects.create(username="test_user"), category_1=Book.Category_Choice[0])

        with self.assertRaises(IntegrityError):
            test_author = Author.objects.create()
        with self.assertRaises(IntegrityError):
            test_author = Author.objects.create(book=test_book)
        with self.assertRaises(IntegrityError):
            test_author = Author.objects.create(name=test_name)
        