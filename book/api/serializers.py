from rest_framework import serializers

from account.models import User
from book.models import Author, Book

    
class AddBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [  'title', 'description', 'page_num', 'edition', 'publisher', 
                    'pub_year', 'owner', 'category_1', 'category_2' ,'category_3', 'image']

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [  'title', 'description', 'page_num', 'edition', 'publisher', 
                    'pub_year', 'categories_list', 'authors_list', 'owner_name', 
                    'when_added', ]

class SelfBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [  'title', 'description', 'page_num', 'edition', 'publisher', 
                    'pub_year', 'categories_list', 'authors_list', 'owner_name',
                    'when_added', 'slug', ]

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['name', 'book']

class EditBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [  'title', 'description', 'page_num', 'edition', 'publisher', 
                    'pub_year', 'category_1', 'category_2' ,'category_3', 'image']

class EditBookImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['image']
