from rest_framework import serializers

from account.models import User
from book.models import Author, Book


class BookListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        return [{
                    "title": obj.title,
                    "description": obj.description,
                    "page_num": obj.page_num,
                    "edition": obj.edition,
                    "publisher": obj.publisher,
                    "pub_year": obj.pub_year,
                    "authors_list": obj.authors_list,
                    "owner_name": obj.owner_name,
                    "when_added": obj.when_added,
                    "slug": obj.slug,
                    "rating": obj.rating,
                    "num_rates": obj.num_rates,
                    "num_borrowers": obj.num_borrowers,
                } 
                for obj in data]


class BookResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        list_serializer_class = BookListSerializer


class UserListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        return [{
                    "username": obj.username,
                    "first_name": obj.first_name,
                    "last_name": obj.last_name,
                    "rating": obj.rating,
                    "num_rates": obj.num_rates,
                    "num_borrowers": obj.num_borrowers,
                    "num_lenders": obj.num_lenders,
                } 
                for obj in data]


class UserResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        list_serializer_class = UserListSerializer

